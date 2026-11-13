"""Waveform-channel-selectable KlustaKwik reclustering (Alt+Shift+R)."""

import logging
import math
import os
from pathlib import Path
import shutil
import time
from tempfile import TemporaryDirectory

import numpy as np
from phy import IPlugin, connect
from PyQt5.QtCore import QProcess, QTimer
from PyQt5.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QLabel, QLineEdit, QMessageBox, QProgressDialog, QPushButton,
    QSpinBox, QGridLayout, QHBoxLayout, QWidget, QVBoxLayout,
)

logger = logging.getLogger('phy')
TRAINING_TARGET = 10000


def automatic_subset(n_spikes):
    """KlustaKwik trains on floor(n_spikes / Subset), then labels all spikes."""
    return max(1, math.ceil(n_spikes / TRAINING_TARGET))


def feature_matrix(data, choices):
    """Flatten chosen PCs, preserving the channel ordering used for retrieval."""
    if data is None:
        raise ValueError('PCA features are not available.')
    data = np.asarray(data)
    if data.ndim != 3 or data.shape[1] != len(choices):
        raise ValueError('Unexpected feature array shape.')
    columns = []
    for index, count in enumerate(choices):
        if not 1 <= count <= data.shape[2]:
            raise ValueError('Requested PC count exceeds available features.')
        columns.append(data[:, index, :count])
    matrix = np.concatenate(columns, axis=1)
    if not np.isfinite(matrix).all():
        raise ValueError(
            'Selected channels have missing or non-finite features. Choose other channels.')
    if not np.any(np.ptp(matrix, axis=0) > 0):
        raise ValueError('Selected features have no variation.')
    return matrix


def write_features(path, matrix):
    # One common scale preserves relative feature amplitudes. Avoid int64 extremes.
    scale = np.max(np.abs(matrix))
    values = np.rint(matrix / scale * 1000000).astype(np.int64)
    with open(path, 'w') as stream:
        stream.write(f'{values.shape[1]}\n')
        np.savetxt(stream, values, fmt='%d', delimiter='\t')


def read_labels(path, n_spikes):
    values = np.loadtxt(path, dtype=np.int64, ndmin=1)
    if len(values) != n_spikes + 1 or values[0] < 1 or np.any(values[1:] < 0):
        raise ValueError('KlustaKwik returned an invalid cluster file.')
    return values[1:]


def channel_grid_positions(channels, positions):
    """Preserve electrode offsets, folding after 18 channel-height rows.

    Two grid rows per channel leave room for half-pitch staggered columns.
    Fold all physical columns together to retain their relative alignment.
    """
    positions = np.asarray(positions)
    columns = sorted(set(positions[:, 0]))
    spacings = []
    for x in columns:
        ys = np.unique(positions[positions[:, 0] == x, 1])
        spacings.extend(np.diff(ys))
    if spacings:
        pitch = min(spacings)
    else:
        ys = np.unique(positions[:, 1])
        pitch = min(np.diff(ys)) if len(ys) > 1 else 1.0
    top = positions[:, 1].max()
    result = {}
    for index in range(len(channels)):
        x, y = positions[index]
        row = int(round(2 * (top - y) / pitch))
        result[index] = (row % 36, columns.index(x) + (row // 36) * len(columns))
    return result


def make_channel_selector(channels, labels, positions, n_pcs):
    """Build compact channel controls with the same spatial ordering as waveforms."""
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 0, 0, 0)
    toggle = QPushButton('Select all')
    layout.addWidget(toggle)
    grid = QGridLayout()
    grid.setVerticalSpacing(2)
    layout.addLayout(grid)
    checks, counts = [], []
    cells = channel_grid_positions(channels, positions)
    for index, channel in enumerate(channels):
        cell = QWidget()
        row = QHBoxLayout(cell)
        row.setContentsMargins(2, 0, 2, 0)
        check = QCheckBox(str(labels[index]))
        check.setToolTip(f'Channel ID {channel}')
        check.setChecked(False)
        count = QSpinBox()
        count.setRange(1, n_pcs)
        count.setValue(min(3, n_pcs))
        count.setPrefix('PCs: ')
        row.addWidget(check)
        row.addWidget(count)
        grid.addWidget(cell, *cells[index], 2, 1)
        checks.append(check)
        counts.append(count)
    def update_toggle():
        toggle.setText('Deselect all' if all(c.isChecked() for c in checks) else 'Select all')
    def toggle_all():
        select = not all(c.isChecked() for c in checks)
        for check in checks:
            check.setChecked(select)
    toggle.clicked.connect(toggle_all)
    for check in checks:
        check.toggled.connect(update_toggle)
    return panel, checks, counts


class ChannelReclusterPlugin(IPlugin):
    def attach_to_controller(self, controller):
        self._process = None
        self._program = str(
            Path('~/github/klustakwik/KlustaKwik').expanduser())
        if not Path(self._program).is_file():
            self._program = shutil.which('KlustaKwik') or str(
                Path('~/.phy/klustakwik.exe').expanduser())

        @connect
        def on_gui_ready(sender, gui):
            @controller.supervisor.actions.add(shortcut='alt+shift+r')
            def recluster_waveform_channels():
                supervisor = controller.supervisor
                if self._process is not None:
                    gui.status_message = 'KlustaKwik is already running.'
                    return
                if supervisor.selection.state.is_merge_mode:
                    gui.status_message = 'Reclustering is unavailable in Merge mode.'
                    return
                if len(supervisor.selected) != 1:
                    gui.status_message = 'Select exactly one cluster.'
                    return
                view = gui.get_view('WaveformView')
                channels = list(
                    view.channel_ids) if view is not None and view.channel_ids is not None else []
                if not channels:
                    gui.status_message = 'Open a WaveformView with visible channels first.'
                    return
                cluster_id = supervisor.selected[0]
                spike_ids = supervisor.clustering.spikes_in_clusters(
                    [cluster_id]).copy()
                if len(spike_ids) < 2:
                    gui.status_message = 'At least two spikes are required.'
                    return
                probe = controller.model.get_features(spike_ids[:1], channels)
                if probe is None or probe.shape[2] < 1:
                    gui.status_message = 'PCA features are not available.'
                    return
                n_pcs = probe.shape[2]
                dialog = QDialog(gui)
                dialog.setWindowTitle('KlustaKwik reclustering')
                layout = QVBoxLayout(dialog)
                layout.addWidget(QLabel(
                    f'Cluster {cluster_id}: all {len(spike_ids):,} spikes\nChannels from the first WaveformView.'))
                positions = view.canvas.boxed.box_pos
                panel, checks, counts = make_channel_selector(
                    channels, controller._get_channel_labels(channels), positions, n_pcs)
                layout.addWidget(panel)
                form = QFormLayout()
                program = QLineEdit(self._program)
                form.addRow('KlustaKwik executable', program)
                browse = QPushButton('Browse...')

                def choose_program():
                    filename, _ = QFileDialog.getOpenFileName(
                        dialog, 'Choose KlustaKwik executable')
                    if filename:
                        program.setText(filename)
                browse.clicked.connect(choose_program)
                form.addRow('', browse)
                subset = QSpinBox()
                subset.setRange(1, len(spike_ids))
                subset.setValue(automatic_subset(len(spike_ids)))
                form.addRow('Subset (1 = all for training)', subset)
                estimate = QLabel()

                def update_estimate():
                    estimate.setText(
                        f'Train on approximately {len(spike_ids) // subset.value():,} spikes; assign all {len(spike_ids):,}.')
                subset.valueChanged.connect(update_estimate)
                update_estimate()
                form.addRow('', estimate)
                layout.addLayout(form)
                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.button(QDialogButtonBox.Ok).setText('Run')
                def update_run_enabled():
                    buttons.button(QDialogButtonBox.Ok).setEnabled(
                        any(check.isChecked() for check in checks))
                for check in checks:
                    check.toggled.connect(update_run_enabled)
                update_run_enabled()
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                dialog.adjustSize()
                if dialog.exec_() != QDialog.Accepted:
                    return
                subset_value = subset.value()
                chosen = [i for i, check in enumerate(
                    checks) if check.isChecked()]
                if not chosen:
                    gui.status_message = 'Select at least one channel.'
                    return
                executable = Path(program.text()).expanduser()
                if not executable.is_file() or not os.access(executable, os.X_OK):
                    gui.status_message = 'Choose an executable KlustaKwik program.'
                    return
                self._program = str(executable.resolve())
                temp = TemporaryDirectory(prefix='phy-klustakwik-')
                try:
                    data = controller.model.get_features(
                        spike_ids, [channels[i] for i in chosen])
                    matrix = feature_matrix(
                        data, [counts[i].value() for i in chosen])
                    if len(spike_ids) // subset_value <= matrix.shape[1] + 1:
                        raise ValueError(
                            'Too few training spikes for these features. Reduce Subset or PC count.')
                    write_features(Path(temp.name) / 'recluster.fet.1', matrix)
                except Exception as error:
                    temp.cleanup()
                    QMessageBox.warning(gui, 'Reclustering failed', str(error))
                    return
                process = QProcess(gui)
                self._process = process
                progress = QProgressDialog(
                    'Running KlustaKwik on all selected-cluster spikes...', 'Cancel', 0, 0, gui)
                progress.setWindowTitle('KlustaKwik reclustering')
                progress.setAutoClose(False)
                cancelled = [False]
                cleaned = [False]

                def cancel():
                    cancelled[0] = True
                    process.kill()
                progress.canceled.connect(cancel)
                process.setWorkingDirectory(temp.name)
                process.setProcessChannelMode(QProcess.MergedChannels)
                output_tail = ['']

                def read_output():
                    output = bytes(process.readAllStandardOutput()).decode(errors='replace')
                    if output:
                        output_tail[0] = (output_tail[0] + output)[-4000:]
                        for line in output.splitlines():
                            logger.info('KlustaKwik: %s', line)
                process.readyReadStandardOutput.connect(read_output)
                started_at = time.monotonic()
                timer = QTimer(process)
                timer.setInterval(10000)

                def report_running():
                    elapsed = int(time.monotonic() - started_at)
                    message = f'KlustaKwik running: {elapsed} s elapsed (Subset={subset_value}).'
                    progress.setLabelText(message)
                    gui.status_message = message
                    logger.info(message)
                timer.timeout.connect(report_running)
                timer.start()

                def finish(exit_code=1, exit_status=None):
                    if cleaned[0]:
                        return
                    cleaned[0] = True
                    timer.stop()
                    read_output()
                    # QProgressDialog.close() emits canceled, even on normal completion.
                    progress.canceled.disconnect(cancel)
                    progress.close()
                    logger.info('KlustaKwik exited: code=%s, status=%s, elapsed=%.1f s',
                                exit_code, exit_status, time.monotonic() - started_at)
                    try:
                        if cancelled[0]:
                            gui.status_message = 'KlustaKwik reclustering cancelled.'
                            logger.info(gui.status_message)
                            return
                        if exit_code != 0:
                            detail = output_tail[0][-2000:] or process.errorString()
                            raise RuntimeError(
                                f'KlustaKwik failed (exit {exit_code}). {detail}')
                        labels = read_labels(
                            Path(temp.name) / 'recluster.clu.1', len(spike_ids))
                        current = supervisor.clustering.spikes_in_clusters([
                                                                           cluster_id])
                        if not np.array_equal(np.sort(current), np.sort(spike_ids)):
                            raise RuntimeError(
                                'Source cluster changed during processing; results were not applied.')
                        if supervisor.selection.state.is_merge_mode:
                            raise RuntimeError(
                                'Leave Merge mode and run reclustering again.')
                        if len(np.unique(labels)) < 2:
                            gui.status_message = 'KlustaKwik found only one subcluster; no split performed.'
                            logger.info(gui.status_message)
                            return
                        supervisor.actions.split(spike_ids, labels)
                        gui.status_message = f'Reclustered {len(spike_ids):,} spikes into {len(np.unique(labels))} clusters (Subset={subset_value}).'
                        logger.info(gui.status_message)
                    except Exception as error:
                        logger.exception('KlustaKwik reclustering failed')
                        QMessageBox.warning(
                            gui, 'Reclustering failed', str(error))
                    finally:
                        temp.cleanup()
                        self._process = None
                        process.deleteLater()
                        progress.deleteLater()
                process.finished.connect(finish)
                process.errorOccurred.connect(
                    lambda error: finish() if error == QProcess.FailedToStart else None)
                args = ['recluster', '1', '-UseDistributional', '0', '-Subset', str(subset_value),
                        '-MinClusters', '2', '-MaxClusters', '10', '-MaxPossibleClusters', '20']
                logger.info('Running KlustaKwik: %d spikes, %d features, Subset=%d', len(
                    spike_ids), matrix.shape[1], subset_value)
                process.start(self._program, args)
                progress.show()

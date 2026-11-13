"""Separate within-cluster or cross-cluster double counts at gaps <= 0.2 ms."""

import logging

import numpy as np
from phy import IPlugin, connect


logger = logging.getLogger('phy')
DOUBLE_COUNT_GAP_SECONDS = 0.0002


def find_double_count_spikes(spike_ids, spike_times):
    """Return later spikes in short adjacent gaps, keeping each chain's first spike.

    Times are in seconds. Equal times retain the first spike in the input order.
    """
    spike_ids = np.asarray(spike_ids, dtype=np.int64)
    spike_times = np.asarray(spike_times, dtype=np.float64)
    order = np.argsort(spike_times, kind='stable')
    times = spike_times[order]
    if len(times) < 2:
        return spike_ids[:0]
    # Allow rounding error when subtracting timestamps late in a recording.
    tolerance = 4 * np.finfo(np.float64).eps * max(1.0, np.max(np.abs(times)))
    duplicate = np.diff(times) <= DOUBLE_COUNT_GAP_SECONDS + tolerance
    return spike_ids[order[1:][duplicate]]


def cross_cluster_double_count_masks(times_a, times_b):
    """Mark both sides of every cross-cluster match, without pairing limits."""
    a = np.asarray(times_a, dtype=np.float64)
    b = np.asarray(times_b, dtype=np.float64)
    scale = max(1.0, np.max(np.abs(a)) if len(a) else 0,
                np.max(np.abs(b)) if len(b) else 0)
    threshold = DOUBLE_COUNT_GAP_SECONDS + 4 * np.finfo(np.float64).eps * scale

    def matches(times, other):
        if not len(other):
            return np.zeros(len(times), dtype=bool)
        other = np.sort(other)
        index = np.searchsorted(other, times)
        left = np.clip(index - 1, 0, len(other) - 1)
        right = np.clip(index, 0, len(other) - 1)
        distance = np.minimum(np.abs(times - other[left]), np.abs(times - other[right]))
        return distance <= threshold

    return matches(a, b), matches(b, a)


class DoubleCountPlugin(IPlugin):
    def attach_to_controller(self, controller):
        @connect
        def on_gui_ready(sender, gui):
            @controller.supervisor.actions.add(shortcut='alt+shift+d')
            def split_double_count_spikes():
                """Split double counts into a separate cluster per selected source cluster."""
                supervisor = controller.supervisor
                cluster_ids = list(dict.fromkeys(supervisor.selected))
                if not cluster_ids:
                    gui.status_message = 'Select at least one cluster.'
                    return
                if len(cluster_ids) > 2:
                    gui.status_message = 'Select no more than two clusters.'
                    return
                if supervisor.selection.state.is_merge_mode:
                    gui.status_message = 'Double-count splitting is unavailable in Merge mode.'
                    return

                spikes = [np.asarray(supervisor.clustering.spikes_in_clusters([cid]),
                                     dtype=np.int64) for cid in cluster_ids]
                times = [controller.model.spike_times[ids] for ids in spikes]
                if len(cluster_ids) == 1:
                    duplicate_ids = find_double_count_spikes(spikes[0], times[0])
                    masks = [np.isin(spikes[0], duplicate_ids)]
                else:
                    masks = cross_cluster_double_count_masks(*times)

                if not any(np.any(mask) for mask in masks):
                    gui.status_message = 'No double-count spikes found (gap <= 0.2 ms).'
                    return

                # Explicitly label ALL source spikes: Phy otherwise assigns the
                # unlisted remainder IDs after the duplicate IDs. Keep remainders
                # first (A, B), then duplicates (A, B), in ascending new-ID order.
                parts, labels = [], []
                for duplicate in (False, True):
                    for ids, mask in zip(spikes, masks):
                        part = ids[mask if duplicate else ~mask]
                        if len(part):
                            labels.append(np.full(len(part), len(parts), dtype=np.int64))
                            parts.append(part)
                supervisor.actions.split(np.concatenate(parts), np.concatenate(labels))
                message = (
                    f'Split {sum(np.count_nonzero(mask) for mask in masks)} double-count '
                    f'spikes; {len(parts)} resulting clusters, non-duplicates first '
                    f'(gap <= 0.2 ms).'
                )
                for cid, mask in zip(cluster_ids, masks):
                    if len(mask) and np.all(mask):
                        message += f' All spikes in cluster {cid} matched cross-cluster double counts.'
                gui.status_message = message
                logger.info(message)

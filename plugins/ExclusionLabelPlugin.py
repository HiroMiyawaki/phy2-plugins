"""Manually toggle exclusion=doubled on selected clusters (Alt+Shift+E)."""

import logging

from phy import IPlugin, connect


logger = logging.getLogger('phy')


class ExclusionLabelPlugin(IPlugin):
    def attach_to_controller(self, controller):
        @connect
        def on_gui_ready(sender, gui):
            @controller.supervisor.actions.add(shortcut='alt+shift+e')
            def toggle_doubled_exclusion():
                """Toggle each selected cluster's exclusion label independently."""
                supervisor = controller.supervisor
                cluster_ids = list(dict.fromkeys(supervisor.selected))
                if not cluster_ids:
                    gui.status_message = 'Select at least one cluster.'
                    return
                if supervisor.selection.state.is_merge_mode:
                    gui.status_message = 'Exclusion labeling is unavailable in Merge mode.'
                    return

                meta = supervisor.cluster_meta
                has_field = 'exclusion' in meta.fields
                mark, clear = [], []
                for cluster_id in cluster_ids:
                    value = meta.get('exclusion', cluster_id) if has_field else None
                    (clear if value == 'doubled' else mark).append(cluster_id)

                # Use Phy's label operation for table refresh, Undo, and normal TSV saving.
                # Snapshot both groups before modifying either one.
                if mark:
                    supervisor.label('exclusion', 'doubled', cluster_ids=mark)
                if clear:
                    supervisor.label('exclusion', None, cluster_ids=clear)
                message = (
                    f'Exclusion: marked {len(mark)} cluster(s) as doubled; '
                    f'cleared {len(clear)} cluster(s). Save with Ctrl+S.'
                )
                gui.status_message = message
                logger.info(message)

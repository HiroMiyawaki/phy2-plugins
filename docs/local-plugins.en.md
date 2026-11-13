# Local additions and modifications

[日本語](local-plugins.ja.md) · [Repository README](../README.md)

This guide documents changes in this working copy relative to the cloned repository. It does not claim authorship of inherited plugins. The repository has not yet been forked or published by these documentation changes.

## Provenance

| Status | File / plugin | Scope |
|---|---|---|
| Newly added here | `WaveformChannelsPlugin.py` / `WaveformChannelsPlugin` | Increase model waveform-channel candidates from the installed default of 12 to 32 |
| Newly added here | `DoubleCountPlugin.py` / `DoubleCountPlugin` | Within-cluster and cross-cluster duplicate candidate separation |
| Newly added here | `ChannelReclusterPlugin.py` / `ChannelReclusterPlugin` | Channel-selectable KlustaKwik reclustering |
| Newly added here | `ExclusionLabelPlugin.py` / `ExclusionLabelPlugin` | Manual `exclusion=doubled` toggle |
| Inherited, modified here | `CustomActionPlugin.py` / `CustomActionPlugin` | Fix unsorted-cluster lookup and report when none exists |
| Inherited, modified in this working copy | `recluster.py` / `Recluster` | Local KlustaKwik executable path and process/thread settings; not a newly authored plugin |

Other existing plugins, including ImprovedISIAnalysis, StableMahalanobisDetection, ReclusterUMAP, GoodLabelsPlugin, RawDataFilterPlugin, and SplitShortISI, are inherited from the cloned repository. Their presence is not a new contribution documented here. Original credits remain in the README.

## Installation and saving

1. Use the Python environment in which Phy is installed. WaveformChannelsPlugin uses Phy; the other three new plugins use NumPy and Phy; ChannelReclusterPlugin also uses PyQt5 and a separate KlustaKwik executable.
2. Copy the desired new `.py` files from `plugins/` into `~/.phy/plugins/` (typically `%USERPROFILE%\.phy\plugins\` on Windows).
3. Add their class names to the **existing** `c.TemplateGUI.plugins` list in your active Phy configuration. Preserve the other entries:

   ```python
   'WaveformChannelsPlugin',
   'DoubleCountPlugin',
   'ChannelReclusterPlugin',
   'ExclusionLabelPlugin',
   ```

4. Restart Phy. The repository's example `phy_config.py` includes the other three entries; add `'WaveformChannelsPlugin'` yourself to enable this startup adjustment.
5. Save curation changes with Phy's Save action / Ctrl+S. Copying updated source files alone does not update an already running Phy session.

The three action plugins display English messages and reject their editing actions in Merge mode. WaveformChannelsPlugin applies its settings on attachment without a shortcut. On macOS, Alt means Option. Shortcuts may need adjustment if your environment intercepts them.

### Obtaining KlustaKwik

The standalone executable and source ZIP are no longer bundled. Obtain and build the command-line program using the [upstream KlustaKwik instructions](https://github.com/klusta-team/klustakwik) (repository marked unmaintained). ChannelReclusterPlugin uses its `.fet` / `.clu` interface; other klusta-related packages are not automatic substitutes. Select your executable with Browse. Local binaries, downloaded archives, and generated clustering files are ignored by Git. Earlier inherited commits still contain the original bundled files; this change does not rewrite history.

## WaveformChannelsPlugin

Source: [WaveformChannelsPlugin.py](../plugins/WaveformChannelsPlugin.py). This is a **new local addition**, not an inherited plugin. Class name for configuration: **`WaveformChannelsPlugin`** (matching the filename stem).

At attachment to the controller, it sets:

```python
controller.model.n_closest_channels = 32
controller.model.amplitude_threshold = 0
```

The locally installed `phylib/io/model.py` defines `TemplateModel.n_closest_channels = 12` and `amplitude_threshold = 0`. Thus the channel candidate limit changes from **12 to 32** in this environment; the threshold is explicitly kept at zero. Defaults can differ across installations or local modifications.

This expands the nearby-channel candidates used by model-based waveform channel selection. It does **not** guarantee exactly 32 displayed channels or impose a total limit across multiple selected clusters: available channels, shank restrictions, stored data, and the view's channel-selection path can reduce or otherwise affect the displayed set. It changes the shared model settings, rather than only resizing a WaveformView widget.

There is no shortcut or settings dialog. Enable the class in `c.TemplateGUI.plugins` and restart Phy. A startup message prints `n_closest_channels = 32`. To change the value, edit `WaveformChannelsPlugin.py`, copy the updated file to your plugin directory, and restart. To restore the environment's normal defaults, remove the class from the enabled-plugin list and restart; this plugin does not modify installed Phy/phylib source files.

ChannelReclusterPlugin takes its candidates from the actual first WaveformView, so this plugin can expand the channels available in its selection dialog. It does not generate missing PCA features for newly displayed channels. More displayed channels may increase rendering and data-loading work.

## DoubleCountPlugin

Source: [DoubleCountPlugin.py](../plugins/DoubleCountPlugin.py). Shortcut: **Alt+Shift+D**.

Select one or two clusters, then invoke the shortcut. Selection includes the main (best) and similarity views, with repeated IDs counted once. All spikes of each selected cluster are used.

### One selected cluster

Spikes are sorted by time. In every adjacent gap of **0.2 ms or less**, the later spike is separated as a duplicate candidate. Equal timestamps retain the first spike in input order. A connected chain retains only its first spike: at 0, 0.15, and 0.30 ms, both the second and third spikes are separated even though the first-to-third gap exceeds 0.2 ms.

The resulting new IDs place non-duplicates before duplicate candidates.

### Two selected clusters

Only **cross-cluster** matches are checked in this mode. Every spike within 0.2 ms of any spike in the other cluster is marked on both sides. Matches are not constrained to one-to-one pairs; a spike matching multiple others is separated only once. The within-cluster rule is not additionally applied.

New cluster IDs are assigned in this order, omitting empty groups:

1. A non-duplicates
2. B non-duplicates
3. A duplicate candidates
4. B duplicate candidates

Usually four clusters result. If all spikes on one side match, three result; if all spikes on both sides match, two result. The status message reports fully matched source clusters. This order is visible when sorting by cluster ID ascending; other table sorts may show a different order.

### No matches and review

With no matches, selection and assignments remain unchanged and a status message is shown. With no selection, or more than two selected clusters, the action only displays guidance. Successful separation is a single Phy split operation and supports Undo.

**This plugin separates candidates; it neither deletes spikes nor automatically marks them for exclusion.** In particular, cross-cluster coincidence alone does not establish duplication. Inspect waveforms and spatial distributions, and retain one valid representation of a true firing event before marking unwanted candidates manually.

## ChannelReclusterPlugin

Source: [ChannelReclusterPlugin.py](../plugins/ChannelReclusterPlugin.py). Shortcut: **Alt+Shift+R**.

Select exactly one cluster and open a WaveformView, then invoke the shortcut.

### Channel and feature selection

- Candidates come from the **first WaveformView** if multiple views are open.
- Channels start **unselected**. Run is disabled until at least one is selected. Select all / Deselect all provides a bulk toggle; Cancel remains available.
- Each channel defaults to the first **3 PCs**, or all available PCs if fewer than three exist. PC counts can be changed independently.
- The layout uses WaveformView's channel coordinates, including staggered columns. It uses half-channel-height grid steps and folds after 18 channel-height rows. This is a compact representation rather than a scale drawing of arbitrary electrode geometry.
- Tooltips show internal channel IDs; checkbox text shows channel labels. Features are retrieved through the model's channel-aware API.

### All spikes and Subset

The full selected cluster is supplied to KlustaKwik. The current automatic default is:

```text
Subset = max(1, ceil(number_of_spikes / 10000))
```

| Spikes | Default Subset | Approximate training count |
|---:|---:|---:|
| 1,467 | 1 | 1,467 |
| 10,000 | 1 | 10,000 |
| 50,000 | 5 | 10,000 |
| 100,000 | 10 | 10,000 |

KlustaKwik trains on `floor(number_of_spikes / Subset)` spikes and assigns labels to the **whole input**, including spikes outside the training subset. Change Subset in the dialog; 1 trains on everything. Smaller training subsets trade speed for the ability to resolve rare populations. Too few training spikes for the selected feature dimensionality are rejected.

### Executable and processing

The plugin first looks for `~/github/klustakwik/KlustaKwik`, then `KlustaKwik` on PATH, then `~/.phy/klustakwik.exe`. Use Browse to choose your actual executable. Its location is remembered for the current controller session, not saved as a persistent preference.

The executable must support the KlustaKwik `.fet` / `.clu` interface and these arguments:

```text
-UseDistributional 0 -Subset N -MinClusters 2 -MaxClusters 10 -MaxPossibleClusters 20
```

The result is not guaranteed to contain a particular number of clusters. Selected PCs are concatenated, scaled by one common factor, and written as integer features in a temporary directory. Missing/non-finite features and entirely constant inputs are rejected.

Feature loading and input-file preparation occur on the GUI thread. The external process then runs asynchronously with a cancellable progress dialog. Console output is forwarded when available, with a running message every 10 seconds and an exit/result message. The executable may buffer its output; a heartbeat alone does not prove computational progress.

A valid multi-cluster result is applied as one undoable split. A single-cluster result leaves assignments unchanged. Cancellation or process failure does not apply results. If the source cluster membership changed during execution, or Merge mode is active at completion, results are rejected. Temporary files are cleaned up afterward. These checks do not lock the source against editing while the process runs.

## ExclusionLabelPlugin

Source: [ExclusionLabelPlugin.py](../plugins/ExclusionLabelPlugin.py). Shortcut: **Alt+Shift+E**.

After visual review, select the clusters to mark and invoke the shortcut. The toggle is **per cluster**, including main and similarity selections:

| Existing `exclusion` value | New value |
|---|---|
| Unset | `doubled` |
| `doubled` | Unset (`None` internally) |
| Any other value | `doubled` (overwrites the previous value) |

The `exclusion` column is added through Phy's label operation. A selection mixing already marked and unmarked clusters swaps their individual states; it does not force all selected clusters to the same value. An empty selection only displays guidance.

Marking and clearing use Phy's normal history. If both happen in one invocation, **two Undo steps** are needed to revert the entire invocation. Save with Ctrl+S to persist the label in the dataset's `cluster_exclusion.tsv`. Unset values are omitted from that metadata file; unlisted clusters are not marked.

Equivalent manual labeling: select clusters, press **L**, and enter:

```text
exclusion doubled
```

This plugin does not delete or filter any spikes. Downstream code must read `cluster_exclusion.tsv` and remove spikes whose current `spike_clusters.npy` cluster ID has `exclusion == doubled`, **before** computing final analysis/QC metrics. Keep the original data and record removed counts. Artifact notes should not automatically trigger this double-count exclusion rule. Recheck labels after later splits or merges because Phy may propagate metadata to descendants.

## Changes to inherited plugins

### CustomActionPlugin

Source: [CustomActionPlugin.py](../plugins/CustomActionPlugin.py). This is an existing upstream plugin, not a new plugin created here.

The Ctrl+C action now retrieves the group for each displayed cluster ID directly. This fixes the out-of-range lookup and handles empty lists and non-contiguous IDs. It selects the first displayed nonempty cluster with group unset or `unsorted`; when none exists, it keeps the selection and displays `No unsorted clusters found.` The existing Ctrl+V and Ctrl+B actions were not changed by this fix.

### Recluster

Source: [recluster.py](../plugins/recluster.py). This is the inherited legacy plugin and is separate from the new ChannelReclusterPlugin.

The current working-copy changes affect the local-PCA action (Alt+Shift+K): the non-Windows executable path is expanded from `~/github/klustakwik/KlustaKwik`; execution uses `subprocess.run(..., check=True)` with `OMP_NUM_THREADS=12` and `OMP_DYNAMIC=FALSE`. These are local environment settings, not a portable executable-discovery mechanism or a guarantee of twelve active threads. The action remains synchronous. These changes do not add channel selection, automatic Subset, or the new progress dialog to the legacy plugin. The global-PCA action was not modernized by these changes.

## Suggested workflow

1. Inspect a cluster; optionally recluster it with ChannelReclusterPlugin.
2. Separate within-cluster or cross-cluster duplicate candidates with DoubleCountPlugin.
3. Review the separated candidates and decide which detections are redundant.
4. Manually toggle `exclusion=doubled` only on clusters intended for removal.
5. Save in Phy, then apply the explicit label-based filter in downstream analysis/QC.

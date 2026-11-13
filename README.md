# Plugins to Phy2
These plugins add additional features to Phy2. Originally created for Phy1 by Peter Petersen and made compatible with Phy2 by Thomas Hainmueller. Newly updated implementations made by Mingze Dou.

## Features

### Additions in this working copy / 今回の新規追加

These four plugins were added locally after cloning. They are separate from the inherited plugins listed below. See the bilingual guides for installation, behavior, and limitations.

| New plugin | Shortcut | Documentation |
|---|---|---|
| WaveformChannelsPlugin — increase waveform channel candidates to 32 | Applied at startup | [English](docs/local-plugins.en.md#waveformchannelsplugin) / [日本語](docs/local-plugins.ja.md#waveformchannelsplugin) |
| DoubleCountPlugin — separate duplicate candidates | `alt+shift+d` | [English](docs/local-plugins.en.md#doublecountplugin) / [日本語](docs/local-plugins.ja.md#doublecountplugin) |
| ChannelReclusterPlugin — channel-selectable KlustaKwik | `alt+shift+r` | [English](docs/local-plugins.en.md#channelreclusterplugin) / [日本語](docs/local-plugins.ja.md#channelreclusterplugin) |
| ExclusionLabelPlugin — manual `exclusion=doubled` toggle | `alt+shift+e` | [English](docs/local-plugins.en.md#exclusionlabelplugin) / [日本語](docs/local-plugins.ja.md#exclusionlabelplugin) |

ChannelReclusterPlugin starts with no channels selected, defaults to 3 PCs per channel, and currently uses `Subset = max(1, ceil(n_spikes / 10000))`. DoubleCountPlugin does not automatically add exclusion labels. Downstream analysis/QC must explicitly apply the exclusion filter.

### Local modifications to inherited plugins / 既存プラグインの修正

These are modifications to existing code, not newly authored plugins:

* **CustomActionPlugin**: Fixed unsorted-cluster lookup and added a no-match status message. [English](docs/local-plugins.en.md#customactionplugin) / [日本語](docs/local-plugins.ja.md#customactionplugin)
* **Recluster** (`plugins/recluster.py`): Local-PCA executable path and process/thread settings changed in this working copy. This legacy plugin is distinct from ChannelReclusterPlugin. [English](docs/local-plugins.en.md#recluster) / [日本語](docs/local-plugins.ja.md#recluster)

Full change provenance and usage: [English guide](docs/local-plugins.en.md) / [日本語ガイド](docs/local-plugins.ja.md).

### Inherited features from the cloned repository

The following features were already present in the cloned repository; they are not new contributions in this working copy.

* **ImprovedISIAnalysis** (`alt+i`): Detects ISI conflicts using multiple metrics
* **StableMahalanobisDetection** (`alt+x`): Outlier detection with interactive visualization
* **ReclusterUMAP** (`alt+k`): Modern reclustering using UMAP and template matching
* **GoodLabelsPlugin**: Improved cluster organization that sorts by quality (good > mua > noise). Provides better workflow organization despite Phy's real-time update limitations.

### Inherited legacy features
* **Reclustering** (`alt+shift+k`, `alt+shift+t`): KlustaKwik 2.0 based reclustering
* **Mahalanobis Distance** (`alt+shift+x`): Outlier detection (threshold: 16 std)
* **K-means Clustering** (`alt+shift+q`): Basic clustering with adjustable clusters
* **ISI Violation** (`alt+shift+i`): Visualize refractory period violations

## Dependencies
```bash
pip install pandas numpy scipy scikit-learn umap-learn
```

## Installation
1. Copy the plugin files from the `plugins` directory of this repository to your Phy user configuration directory, inside a `plugins` subfolder.
   - On Windows, this is typically `C:\Users\<YourUserName>\.phy\plugins`.
   - If the `plugins` folder doesn't exist, you will need to create it.
2. Merge the required entries from `phy_config.py` into your active Phy configuration in `~/.phy/` (Windows: `%USERPROFILE%\.phy\`). Obtain KlustaKwik separately if using a KlustaKwik-based plugin; see below.
3. Install dependencies (see [Dependencies](#dependencies) section above).
4. Copy 'tempdir.py' (from the `plugins` directory of this repository) to `*YourPhyDirectory*/phy/utils`.

## KlustaKwik (external dependency)

KlustaKwik executables and source archives are not bundled in this working tree. Obtain the standalone program from the [upstream KlustaKwik repository](https://github.com/klusta-team/klustakwik), following its build instructions for your platform. That repository is marked unmaintained. These plugins require its command-line `.fet` / `.clu` interface; installing another package named klusta or klustakwik2 does not by itself provide a compatible executable.

For ChannelReclusterPlugin, select the built executable with **Browse** in the dialog. For the inherited Recluster plugin, configure the executable paths in `plugins/recluster.py`; its Windows path expects `klustakwik.exe` in the Phy configuration directory. Follow upstream instructions for building rather than committing local binaries or archives.

KlustaKwik の実行ファイル・ソース ZIP は同梱しません。[配布元](https://github.com/klusta-team/klustakwik)の手順で別途入手・ビルドしてください。ChannelReclusterPlugin は **Browse** で実行ファイルを指定し、従来の Recluster はソース内の実行パスを設定します。

The upstream binaries and archive remain in the inherited Git history. Removing them from the current tree does not erase earlier commits; no history rewrite is performed here.

## Authors
- Original Phy1: Peter Petersen
- Phy2 compatibility: Thomas Hainmueller
- New implementations: Mingze Dou

## How to Cite
[![DOI](https://zenodo.org/badge/126424002.svg)](https://zenodo.org/badge/latestdoi/126424002)

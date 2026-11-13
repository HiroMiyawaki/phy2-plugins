# 今回の追加・修正プラグイン

[English](local-plugins.en.md) · [README](../README.md)

この文書は、クローンしたリポジトリを基準とする、現在の作業コピーの追加・修正を説明します。

## 由来と変更範囲

| 区分 | ファイル / プラグイン | 内容 |
|---|---|---|
| 今回新規追加 | `WaveformChannelsPlugin.py` / `WaveformChannelsPlugin` | 波形表示用のモデルの近傍チャネル候補数を、確認した標準値12から32へ変更 |
| 今回新規追加 | `DoubleCountPlugin.py` / `DoubleCountPlugin` | クラスタ内・クラスタ間の重複候補の分離 |
| 今回新規追加 | `ChannelReclusterPlugin.py` / `ChannelReclusterPlugin` | チャネルを選択できる KlustaKwik 再クラスタリング |
| 今回新規追加 | `ExclusionLabelPlugin.py` / `ExclusionLabelPlugin` | 手動での `exclusion=doubled` 切り替え |
| フォーク元の既存実装を今回修正 | `CustomActionPlugin.py` / `CustomActionPlugin` | unsorted 検索の範囲外参照修正と対象なしの表示 |
| フォーク元の既存実装に作業コピー内の変更あり | `recluster.py` / `Recluster` | ローカルの実行パス・プロセス起動・スレッド設定の変更。今回の新規プラグインではない |

ImprovedISIAnalysis、StableMahalanobisDetection、ReclusterUMAP、GoodLabelsPlugin、RawDataFilterPlugin、SplitShortISI など、その他の既存プラグインはクローン元から継承したものです。今回の新規貢献には含めません。元の作者へのクレジットは README に保持しています。

## 導入と保存

1. Phy がインストールされている Python 環境を使います。WaveformChannelsPlugin は Phy、その他の新規3プラグインは NumPy と Phy、ChannelReclusterPlugin は加えて PyQt5 と別途用意した KlustaKwik 実行ファイルを使います。
2. 必要な新規 `.py` ファイルを `plugins/` から `~/.phy/plugins/` にコピーします。Windows では通常 `%USERPROFILE%\.phy\plugins\` です。
3. 使用中の Phy 設定の **既存の** `c.TemplateGUI.plugins` リストに、必要なクラス名を追記します。他の項目は保持してください。

   ```python
   'WaveformChannelsPlugin',
   'DoubleCountPlugin',
   'ChannelReclusterPlugin',
   'ExclusionLabelPlugin',
   ```

4. Phy を再起動します。リポジトリの設定例 `phy_config.py` には他の3本は登録済みですが、この起動時設定を有効にするには `'WaveformChannelsPlugin'` を追記してください。
5. 編集結果は Phy の Save 操作 / Ctrl+S で保存します。ソースのコピーだけでは実行中の Phy に変更は反映されません。

操作を追加する新規3プラグインの表示は英語です。Merge モードでは編集操作を受け付けません。WaveformChannelsPlugin はショートカットを持たず、コントローラへの接続時に設定を適用します。Mac の Alt は Option キーです。環境側がショートカットを使用している場合は変更が必要です。

### KlustaKwik の入手

単体実行ファイルとソース ZIP の同梱を終了しました。[KlustaKwik の配布元](https://github.com/klusta-team/klustakwik)（メンテナンス終了の表示あり）の手順で、コマンドライン版を入手・ビルドしてください。ChannelReclusterPlugin はその `.fet` / `.clu` インターフェースを使うため、別の klusta 関連パッケージを導入するだけでは代用できません。Browse で実行ファイルを指定します。ローカルの実行ファイル・ダウンロード ZIP・クラスタリング生成物は Git の除外対象です。継承した過去のコミットには元の同梱物が残っており、今回の変更では履歴を書き換えません。

## WaveformChannelsPlugin

ソース：[WaveformChannelsPlugin.py](../plugins/WaveformChannelsPlugin.py)。フォーク元からの継承ではなく、**今回の新規追加**です。設定に登録するクラス名は **`WaveformChannelsPlugin`** で、ファイル名の拡張子を除いた名前と一致します。

コントローラへの接続時に次の値を設定します。

```python
controller.model.n_closest_channels = 32
controller.model.amplitude_threshold = 0
```

ローカルにインストールされた `phylib/io/model.py` で、`TemplateModel.n_closest_channels = 12`、`amplitude_threshold = 0` を確認しました。この環境では近傍チャネル候補数を **12から32** に変更し、振幅のしきい値は明示的に0に保ちます。標準値は導入バージョンやローカルの変更によって異なる場合があります。

モデルに基づく波形表示のチャネル選択で使う、近傍チャネルの候補を増やします。**常に32チャネル表示されることや、複数クラスタ選択時の表示総数の上限を保証するものではありません。** 利用可能なチャネル、shank の制限、保存データ、ビュー側の選択処理によって実際の表示集合は変わります。WaveformView の見た目だけでなく、共有するモデルの設定を変更します。

ショートカットや設定ダイアログはありません。`c.TemplateGUI.plugins` にクラス名を追加して Phy を再起動すると適用され、起動時に `n_closest_channels = 32` を表示します。値を変える場合は `WaveformChannelsPlugin.py` を編集し、プラグインディレクトリにコピーして再起動します。環境の通常の標準値へ戻す場合は有効化リストからクラス名を外して再起動してください。インストール済みの Phy/phylib のソースを書き換えるプラグインではありません。

ChannelReclusterPlugin は実際の最初の WaveformView から候補を取得するため、選択可能なチャネルが増える場合があります。ただし、新たに表示されるチャネルの欠損 PCA feature を生成する機能はありません。表示チャネルを増やすと描画や読み込みの負荷が増える場合があります。

## DoubleCountPlugin

ソース：[DoubleCountPlugin.py](../plugins/DoubleCountPlugin.py)。ショートカット：**Alt+Shift+D**。

1個または2個のクラスタを選択して実行します。main（best）と similarity の選択を含み、同じクラスタ ID は重複して数えません。各クラスタの全スパイクを使います。

### 1クラスタ選択時

時刻順で隣接するスパイクの間隔が **0.2 ms 以下**なら、後のスパイクを重複候補として分離します。同一時刻では入力順の先頭を残します。短い間隔が連鎖する場合は先頭の1個だけを残します。例えば 0、0.15、0.30 ms では、最初から最後までの間隔が 0.2 ms を超えていても、2個目と3個目を分離します。

新しいクラスタ ID は「非重複 → 重複候補」の順になります。

### 2クラスタ選択時

このモードでは **クラスタ間のみ**を比較します。相手クラスタのいずれかのスパイクと 0.2 ms 以下の時間差を持つスパイクを、両側で候補にします。対応は1対1に限定しません。複数スパイクに対応しても分離は1回です。クラスタ内の判定は追加では行いません。

新しいクラスタ ID は、空のグループを省いて次の順に割り当てます。

1. A の非重複
2. B の非重複
3. A の重複候補
4. B の重複候補

通常は4クラスタです。片側の全スパイクが該当すると3クラスタ、両側の全スパイクが該当すると2クラスタになります。全スパイクが該当した元クラスタはステータス表示で通知します。この順序はクラスタ ID の昇順表示に対応し、別の列でソートしている場合の表示順は異なります。

### 対象なしと確認

候補がなければ選択・所属を変えず、ステータスだけ表示します。無選択または3クラスタ以上では案内を表示して終了します。分離は1回の Phy の split 操作として行い、Undo に対応します。

**候補を分離するだけで、スパイクの削除や除外ラベルの自動付与はしません。** 特にクラスタ間の時間的一致だけでは重複と確定できません。波形・空間分布を確認し、実際の発火を1回は残すよう判断してから、不要な候補を手動でマークしてください。

## ExclusionLabelPlugin

ソース：[ExclusionLabelPlugin.py](../plugins/ExclusionLabelPlugin.py)。ショートカット：**Alt+Shift+E**。

目視確認後、マークしたいクラスタを選択して実行します。main と similarity の選択を含め、**クラスタごとに**切り替えます。

| 現在の `exclusion` | 変更後 |
|---|---|
| 未設定 | `doubled` |
| `doubled` | 未設定（内部では `None`） |
| その他の値 | `doubled`（以前の値を上書き） |

Phy のラベル操作で `exclusion` 列を追加します。付与済み・未付与が混在する選択ではそれぞれの状態を反転し、全てを同じ値には揃えません。無選択の場合は案内だけ表示します。

付与と解除は Phy の通常の履歴に記録します。1回の操作に両方が含まれる場合は、全体を戻すために **Undo が2回**必要です。Ctrl+S でデータフォルダの `cluster_exclusion.tsv` に保存します。未設定値はこのメタデータファイルから省略され、記載のないクラスタはマークされていない扱いです。

標準のラベル操作でも同じ値を付けられます。クラスタを選んで **L** を押し、次を入力してください。

```text
exclusion doubled
```

このプラグインはスパイクの削除・フィルタリングを行いません。後続処理で `cluster_exclusion.tsv` と現在の `spike_clusters.npy` を照合し、`exclusion == doubled` のクラスタのスパイクを **最終解析・QC の計算前に除外**してください。元データと除去数も保持します。アーティファクトの注記を、この重複除外ルールに自動的に含めないでください。Phy が分割・マージ先へメタデータを継承する場合があるため、後の編集時にはラベルも再確認してください。


## ChannelReclusterPlugin

ソース：[ChannelReclusterPlugin.py](../plugins/ChannelReclusterPlugin.py)。ショートカット：**Alt+Shift+R**。

クラスタを1個選択し、WaveformView を開いて実行します。
Klustaのリクラスタリングに近い機能を提供します。

### チャネルと feature の選択

- 候補は **最初の WaveformView** の表示チャネルです。複数開いている場合も最初のビューを参照します。
- 初期状態は **全チャネル無選択**です。1つ以上選ぶまで Run は無効です。Select all / Deselect all で一括切り替えでき、Cancel は使用可能です。
- 各チャネルの初期値は **先頭3 PC** です。保存されている PC が3個未満なら利用可能な全 PC になります。チャネルごとに数を変更できます。
- WaveformView のチャネル座標を使い、列間の段ズレを反映します。半チャネル高単位のグリッドに配置し、18チャネル高で折り返します。任意の電極形状を厳密な縮尺で再現する図ではありません。
- チェックボックスにはチャネルラベル、ツールチップには内部 ID を表示します。feature はモデルのチャネル対応 API で取得します。

### 全スパイクと Subset

対象クラスタの全スパイクを KlustaKwik に渡します。現在の自動初期値は次のとおりです。

```text
Subset = max(1, ceil(スパイク数 / 10000))
```

| スパイク数 | 初期 Subset | 学習対象数の目安 |
|---:|---:|---:|
| 1,467 | 1 | 1,467 |
| 10,000 | 1 | 10,000 |
| 50,000 | 5 | 10,000 |
| 100,000 | 10 | 10,000 |

KlustaKwik は `floor(スパイク数 / Subset)` 個で学習し、その結果で学習対象外を含む **全入力スパイク**にラベルを付けます。ダイアログで倍率を変更でき、1なら全スパイクで学習します。学習対象を減らすと高速になる一方、少数の集団を捉えにくくなる場合があります。選択 feature の次元数に対して学習対象が少なすぎる設定は拒否します。

### 実行ファイルと処理

最初に `~/github/klustakwik/KlustaKwik`、次に PATH 上の `KlustaKwik`、最後に `~/.phy/klustakwik.exe` を候補にします。Browse で実際の実行ファイルを選んでください。パスは現在のコントローラのセッション中だけ記憶し、永続的な設定としては保存しません。

実行ファイルは KlustaKwik の `.fet` / `.clu` 形式と次の引数に対応している必要があります。

```text
-UseDistributional 0 -Subset N -MinClusters 2 -MaxClusters 10 -MaxPossibleClusters 20
```

これらは最終的なクラスタ数を保証する設定ではありません。選択した PC を連結し、共通の倍率で整数化して一時ディレクトリへ書き込みます。欠損・非有限値を含む feature や、全列が一定値の入力は拒否します。

feature の読み込みと入力ファイル作成は GUI スレッド上で行います。その後、外部プロセスを非同期で実行し、進捗画面からキャンセルできます。コンソールへ取得可能な出力を転送し、10秒ごとの実行中通知と終了・結果を表示します。実行ファイル側が出力をバッファする場合があるため、定期通知だけでは計算の進行を証明できません。

有効な複数クラスタの結果は1回の Undo 可能な split として反映します。1クラスタだけの結果では所属を変更しません。キャンセル・プロセス失敗時も反映しません。実行中に元クラスタの所属が変わった場合や、完了時に Merge モードの場合は結果を拒否します。終了後は一時ファイルを削除します。これらの確認は、実行中の元クラスタの編集自体をロックするものではありません。

## フォーク元の既存プラグインへの変更

### CustomActionPlugin

ソース：[CustomActionPlugin.py](../plugins/CustomActionPlugin.py)。今回の新規作成ではなく、既存プラグインの修正です。

Ctrl+C の操作で、表示中の各クラスタ ID から直接 group を取得するようにしました。これにより範囲外参照を修正し、空の一覧や欠番にも対応しました。表示順で最初の、スパイクを持つ group 未設定または `unsorted` のクラスタを選択します。対象がなければ選択を維持して `No unsorted clusters found.` と表示します。既存の Ctrl+V と Ctrl+B はこの修正では変更していません。

### Recluster

ソース：[recluster.py](../plugins/recluster.py)。新規の ChannelReclusterPlugin とは別の、継承した従来プラグインです。

現在の作業コピーでは local-PCA 操作（Alt+Shift+K）の非 Windows 実行パスを `~/github/klustakwik/KlustaKwik` から展開し、`subprocess.run(..., check=True)` で起動するよう変更されています。環境変数は `OMP_NUM_THREADS=12`、`OMP_DYNAMIC=FALSE` です。ローカル環境向けの設定であり、汎用的な実行ファイル探索や、実際に12スレッドが使われることを保証するものではありません。この操作は同期実行のままです。従来版にチャネル選択、自動 Subset、新しい進捗画面を追加する変更ではありません。global-PCA 操作もこの変更では改修していません。

## 推奨する作業の流れ

1. クラスタを確認し、必要なら ChannelReclusterPlugin で再クラスタリングします。
2. DoubleCountPlugin でクラスタ内・クラスタ間の重複候補を分離します。
3. 候補を目視で確認し、余分な検出を判断します。
4. 除去するクラスタだけに、手動またはExclusionLabelPluginで `exclusion=doubled` を付けます。
5. Phy で保存し、後続の解析・QC 側でラベルに基づく明示的な除外を行います。

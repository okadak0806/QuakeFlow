# QuakeFlow Elyra Pipeline

このディレクトリには、QuakeFlowワークフローをElyraパイプラインとして実装したファイルが含まれています。

## 概要

ElyraはJupyterLabの拡張機能で、視覚的なパイプライン作成・実行を可能にします。このパイプラインは、地震検出・解析のワークフローを以下のステップに分割しています：

1. **設定** - 地域パラメータとワークフロー設定
2. **イベントダウンロード** - 標準地震カタログの取得
3. **観測点ダウンロード** - 地震観測点情報の取得
4. **波形ダウンロード** - 地震波形データの取得
5. **PhaseNet** - P/S波の自動検出
6. **GaMMA** - 検出された波の関連付け
7. **HypoDD** - 地震の精密位置決定
8. **可視化** - 結果の可視化

## ファイル構成

```
kubeflow/
├── quakeflow_elyra.pipeline     # Elyraパイプライン定義ファイル
├── scripts/                     # 各ステップのPythonスクリプト
│   ├── 01_set_config.py        # 設定ファイル生成
│   ├── 02_download_events.py   # イベントダウンロード
│   ├── 03_download_stations.py # 観測点ダウンロード
│   ├── 04_download_waveforms.py # 波形ダウンロード
│   ├── 05_phasenet_picking.py  # PhaseNet実行
│   ├── 06_gamma_association.py # GaMMA実行
│   ├── 07_convert_station.py   # 観測点フォーマット変換
│   ├── 08_convert_phase.py     # 位相フォーマット変換
│   ├── 09_ph2dt.py            # PH2DT実行
│   ├── 10_hypodd.py           # HypoDD実行
│   └── 11_visualization.py     # 可視化
└── README_elyra.md             # このファイル
```

## 使用方法

### 1. Elyraのインストール

```bash
pip install elyra
jupyter lab build
```

### 2. JupyterLabでElyraを起動

```bash
jupyter lab
```

### 3. パイプラインを開く

1. JupyterLabのファイルブラウザで `quakeflow_elyra.pipeline` を開く
2. Elyraのパイプラインエディタが起動します

### 4. ランタイム設定

パイプラインを実行する前に、Kubeflow Pipelinesランタイムを設定する必要があります：

1. JupyterLabの左サイドバーで「Runtimes」タブを選択
2. 「+」ボタンをクリックして新しいランタイムを追加
3. 以下の情報を入力：
   - **Name**: Kubeflow Pipelines
   - **Runtime Type**: KUBEFLOW_PIPELINES
   - **Kubeflow Pipelines API Endpoint**: `http://ml-pipeline-ui:80/pipeline`
   - **Kubeflow Pipelines Engine**: Tekton または Argo

### 5. パイプラインの実行

1. パイプラインエディタで「Run Pipeline」ボタンをクリック
2. 実行パラメータを設定：
   - **region_name**: 解析対象地域（例：Ridgecrest, Japan）
   - **num_parallel**: 並列処理数
3. 「OK」をクリックして実行開始

## パラメータ設定

### 地域設定

現在サポートされている地域：

- **Ridgecrest**: カリフォルニア州リッジクレスト地震
- **Demo**: デモ用短時間データ
- **Japan**: 日本全域（実装予定）

### 環境変数

各スクリプトで使用される主な環境変数：

- `REGION_NAME`: 解析対象地域
- `NUM_PARALLEL`: 並列処理数
- `BUCKET_NAME`: MinIOバケット名
- `S3_URL`: MinIOサーバーURL
- `SECURE`: HTTPS使用フラグ

## 日本データ対応

日本の地震データに対応するため、以下の設定を追加予定：

### JMA（気象庁）データ
```python
if region_name == "Japan_JMA":
    center = (138.0, 36.0)
    client = "JMA"
    network_list = ["N.JMA"]
```

### Hi-net（防災科研）データ
```python
if region_name == "Japan_NIED":
    center = (138.0, 36.0)
    client = "NIED"
    network_list = ["N.NIED"]
```

## トラブルシューティング

### よくある問題

1. **ランタイム接続エラー**
   - Kubeflow Pipelinesサービスが起動していることを確認
   - ネットワーク設定を確認

2. **Docker イメージエラー**
   - 指定されたDockerイメージが利用可能か確認
   - イメージのプルポリシーを確認

3. **データダウンロードエラー**
   - ネットワーク接続を確認
   - FDSNサーバーの状態を確認

### ログの確認

パイプライン実行中のログは、Kubeflow Pipelines UIで確認できます：

1. ブラウザで `http://ml-pipeline-ui:80` にアクセス
2. 実行中のパイプラインを選択
3. 各ステップのログを確認

## 拡張方法

### 新しい地域の追加

1. `scripts/01_set_config.py` に新しい地域設定を追加
2. 必要に応じて観測網やデータソースを設定

### 新しい処理ステップの追加

1. 新しいPythonスクリプトを `scripts/` ディレクトリに作成
2. パイプラインファイルに新しいノードを追加
3. 依存関係を設定

## 参考資料

- [Elyra Documentation](https://elyra.readthedocs.io/)
- [Kubeflow Pipelines](https://www.kubeflow.org/docs/components/pipelines/)
- [QuakeFlow GitHub](https://github.com/wayneweiqiang/QuakeFlow) 
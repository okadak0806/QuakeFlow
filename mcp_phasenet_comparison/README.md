# PhaseNet Comparison MCP Server

MCPサーバーでPhaseNetの検測情報とJMA/USGSの検測情報を比較検証します。

## 概要

このMCPサーバーは以下の機能を提供します：

- **参照カタログダウンロード**: JMA、USGS、NCEDC等からの地震カタログ取得
- **PhaseNet検測結果読み込み**: CSV、GaMMA、ピック形式のサポート
- **イベントマッチング**: 時間・空間・マグニチュード基準での比較
- **性能評価**: 精度、再現率、F1スコア等の計算
- **包括的レポート**: HTMLレポートと可視化の生成
- **完全ワークフロー**: ダウンロードから評価まで自動実行

## インストール

```bash
cd /Users/okadamac/work/QuakeFlow/mcp_phasenet_comparison
npm install
```

## Claude Codeでの使用方法

### 1. Claude Code設定ファイルに追加

`~/.claude/settings.json`に以下を追加：

```json
{
  "mcpServers": {
    "phasenet-comparison": {
      "command": "node",
      "args": ["/Users/okadamac/work/QuakeFlow/mcp_phasenet_comparison/src/index.js"],
      "env": {}
    }
  }
}
```

### 2. 利用可能なツール

#### `download_reference_catalog`
参照地震カタログをダウンロード

```javascript
// 使用例
{
  "source": "jma",
  "start_time": "2024-01-01T00:00:00",
  "end_time": "2024-01-07T23:59:59",
  "min_latitude": 35.0,
  "max_latitude": 36.0,
  "min_longitude": 139.0,
  "max_longitude": 140.0,
  "min_magnitude": 2.0
}
```

#### `load_phasenet_detections`
PhaseNet検測結果を読み込み

```javascript
{
  "file_path": "/path/to/phasenet_results.csv",
  "format": "csv"
}
```

#### `match_events`
イベント間のマッチング実行

```javascript
{
  "reference_events": "[{...}]", // JSON文字列またはファイルパス
  "detected_events": "[{...}]",  // JSON文字列またはファイルパス
  "time_window": 30.0,
  "distance_threshold": 10.0,
  "magnitude_diff_threshold": 1.0
}
```

#### `calculate_performance_metrics`
性能指標を計算

```javascript
{
  "matching_results": "{...}" // マッチング結果のJSON文字列
}
```

#### `generate_comparison_report`
包括的レポートを生成

```javascript
{
  "matching_results": "{...}",
  "metrics": "{...}",
  "output_path": "./report.html",
  "reference_source": "jma"
}
```

#### `run_full_comparison`
完全ワークフローを実行

```javascript
{
  "reference_source": "jma",
  "phasenet_file": "/path/to/detections.csv",
  "start_time": "2024-01-01T00:00:00",
  "end_time": "2024-01-07T23:59:59",
  "region": {
    "min_latitude": 35.0,
    "max_latitude": 36.0,
    "min_longitude": 139.0,
    "max_longitude": 140.0
  },
  "output_dir": "./comparison_results"
}
```

## サポートするデータソース

### 参照カタログ
- **JMA**: 気象庁（NIEDサーバー経由）
- **USGS**: アメリカ地質調査所
- **NCEDC**: 北カリフォルニア地震データセンター
- **IRIS**: 国際地震学研究機関連合
- **SCEDC**: 南カリフォルニア地震データセンター

### PhaseNet検測形式
- **CSV**: 標準的なCSV形式
- **GaMMA**: GaMMA出力形式
- **Picks**: ピック形式

## マッチング基準

- **時間窓**: ±30秒（デフォルト）
- **距離閾値**: 10km（デフォルト）
- **マグニチュード差**: ±1.0（デフォルト）
- **深度差**: ±50km（デフォルト）

## 性能指標

- **精度（Precision）**: TP/(TP+FP)
- **再現率（Recall）**: TP/(TP+FN)
- **F1スコア**: 2×(Precision×Recall)/(Precision+Recall)
- **検測率（Detection Rate）**: Recall
- **誤警報率（False Alarm Rate）**: FP/(TP+FP)

## 出力ファイル

- `comparison_report.html`: 包括的HTMLレポート
- `event_matches.json`: マッチしたイベント詳細
- `performance_metrics.json`: 性能指標
- `unmatched_*.csv`: 未マッチイベント

## 使用例

### Claude Codeでの基本的な使用

```
PhaseNetとJMAの地震カタログを比較したい。
日本の関東地域で2024年1月1日から7日間のデータを使用。
PhaseNetの結果は/path/to/phasenet_results.csvに保存されている。
```

Claude Codeが自動的に適切なMCPツールを選択し実行します。

### 詳細な比較分析

```
run_full_comparison ツールを使用して、
以下の条件で完全な比較ワークフローを実行：
- reference_source: "jma"
- phasenet_file: "/path/to/detections.csv"
- start_time: "2024-01-01T00:00:00"
- end_time: "2024-01-07T23:59:59"
- region: 関東地域の座標
- より厳格なマッチング基準（時間窓20秒、距離5km）
```

## トラブルシューティング

### よくある問題

1. **ネットワークエラー**: カタログサーバーへのアクセス確認
2. **ファイル形式エラー**: CSV形式とカラム名の確認
3. **メモリ不足**: 大量データ処理時のファイル分割
4. **権限エラー**: 出力ディレクトリの書き込み権限確認

### ログの確認

```bash
# サーバー実行時のログを確認
node src/index.js 2>&1 | tee server.log
```

## 開発情報

- **言語**: JavaScript (Node.js)
- **フレームワーク**: @modelcontextprotocol/sdk
- **依存関係**: axios, csv-parser, haversine等
- **ライセンス**: MIT

## 貢献

バグ報告や機能要求はGitHubリポジトリにお願いします。

## 関連リンク

- [QuakeFlow](https://github.com/quakeflow/quakeflow)
- [PhaseNet](https://github.com/AI4EPS/PhaseNet)
- [MCP Protocol](https://modelcontextprotocol.io/)
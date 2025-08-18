# PhaseNet比較MCPサーバー 使用方法ガイド

## 📋 目次
- [概要](#概要)
- [インストールと設定](#インストールと設定)
- [Claude Codeでの設定](#claude-codeでの設定)
- [基本的な使用方法](#基本的な使用方法)
- [利用可能なツール](#利用可能なツール)
- [実用的な使用例](#実用的な使用例)
- [データ形式とサポート](#データ形式とサポート)
- [トラブルシューティング](#トラブルシューティング)
- [高度な使用方法](#高度な使用方法)

## 📖 概要

PhaseNet比較MCPサーバーは、PhaseNet地震検測結果とJMA/USGSなどの参照カタログを比較検証するためのMCP（Model Context Protocol）サーバーです。

### 主な機能
- 🌐 **多様なカタログソース**: JMA、USGS、NCEDC、IRIS、SCEDCからの地震カタログ取得
- 📊 **精密なマッチング**: 時間・空間・マグニチュード基準での高精度イベント照合
- 📈 **包括的評価**: 精度、再現率、F1スコアなどの詳細な性能指標
- 📄 **美麗なレポート**: インタラクティブなHTMLレポートと可視化
- 🔄 **完全自動化**: ダウンロードから評価まで一括実行

## 🚀 インストールと設定

### 1. 必要要件
- Node.js (v18以上)
- npm
- Claude Code

### 2. インストール
```bash
# リポジトリのクローンまたはダウンロード
cd /path/to/QuakeFlow/mcp_phasenet_comparison

# 依存関係のインストール
npm install

# 動作確認
npm start
```

### 3. ディレクトリ構造
```
mcp_phasenet_comparison/
├── src/
│   ├── index.js                    # メインサーバー
│   └── services/
│       ├── comparison.js           # 比較ロジック
│       ├── catalog-downloader.js   # カタログ取得
│       ├── event-matcher.js        # イベントマッチング
│       └── report-generator.js     # レポート生成
├── sample_data/                    # サンプルデータ
├── results/                        # 結果出力
├── package.json
├── README.md
└── .mcp.json                      # MCP設定
```

## 🔧 Claude Codeでの設定

### プロジェクトレベル設定
プロジェクトディレクトリに `.mcp.json` ファイルを作成：

```json
{
  "mcpServers": {
    "phasenet-comparison": {
      "command": "node",
      "args": ["src/index.js"],
      "cwd": ".",
      "env": {}
    }
  }
}
```

### Claude Code設定の有効化
Claude Codeの設定で以下を確認：

```json
{
  "enableAllProjectMcpServers": true
}
```

または個別に有効化：

```json
{
  "enabledMcpjsonServers": ["phasenet-comparison"]
}
```

## 🎯 基本的な使用方法

### シンプルな比較実行

Claude Codeで以下のようにリクエスト：

```
PhaseNetの検測結果とJMAカタログを比較したい。
日本の関東地域で2024年1月1日から7日間のデータを使用。
PhaseNetの結果は sample_data/phasenet_detections.csv に保存されている。
```

Claude Codeが自動的に適切なツールを選択し、完全な比較ワークフローを実行します。

### より詳細な指定

```
run_full_comparison ツールを使用して完全比較を実行：
- 参照ソース: JMA
- PhaseNetファイル: /path/to/detections.csv
- 期間: 2024年1月1日-7日
- 地域: 関東地域（35-36°N, 139-140°E）
- 厳格なマッチング基準（時間窓20秒、距離5km）
```

## 🛠️ 利用可能なツール

### 1. `download_reference_catalog`
**機能**: 参照地震カタログの取得

**パラメータ**:
```json
{
  "source": "jma|usgs|ncedc|iris|scedc",
  "start_time": "2024-01-01T00:00:00",
  "end_time": "2024-01-07T23:59:59",
  "min_latitude": 35.0,
  "max_latitude": 36.0,
  "min_longitude": 139.0,
  "max_longitude": 140.0,
  "min_magnitude": 2.0,
  "max_magnitude": 9.0
}
```

**使用例**:
```
JMAから関東地域の地震カタログを2024年1月1週間分ダウンロード
```

### 2. `load_phasenet_detections`
**機能**: PhaseNet検測結果の読み込み

**パラメータ**:
```json
{
  "file_path": "/path/to/phasenet_results.csv",
  "format": "csv|gamma|picks"
}
```

**使用例**:
```
PhaseNet検測結果をCSV形式で /path/to/detections.csv から読み込み
```

### 3. `match_events`
**機能**: イベント間のマッチング実行

**パラメータ**:
```json
{
  "reference_events": "参照イベントのJSON文字列またはファイルパス",
  "detected_events": "検測イベントのJSON文字列またはファイルパス",
  "time_window": 30.0,
  "distance_threshold": 10.0,
  "magnitude_diff_threshold": 1.0
}
```

**使用例**:
```
参照カタログと検測結果をマッチング。時間窓30秒、距離10km、マグニチュード差1.0の基準で
```

### 4. `calculate_performance_metrics`
**機能**: 性能指標の計算

**パラメータ**:
```json
{
  "matching_results": "マッチング結果のJSON文字列"
}
```

**算出指標**:
- 精度 (Precision)
- 再現率 (Recall)
- F1スコア
- 検測率
- 誤警報率
- 残差統計

### 5. `generate_comparison_report`
**機能**: 包括的HTMLレポートの生成

**パラメータ**:
```json
{
  "matching_results": "マッチング結果のJSON",
  "metrics": "性能指標のJSON",
  "output_path": "./report.html",
  "reference_source": "参照ソース名"
}
```

**生成内容**:
- インタラクティブな地図表示
- 性能指標の可視化
- 詳細なイベントテーブル
- 残差分析グラフ

### 6. `run_full_comparison` ⭐
**機能**: 完全ワークフローの一括実行

**パラメータ**:
```json
{
  "reference_source": "jma|usgs|ncedc|iris|scedc",
  "phasenet_file": "/path/to/detections.csv",
  "start_time": "2024-01-01T00:00:00",
  "end_time": "2024-01-07T23:59:59",
  "region": {
    "min_latitude": 35.0,
    "max_latitude": 36.0,
    "min_longitude": 139.0,
    "max_longitude": 140.0
  },
  "output_dir": "./results",
  "matching_criteria": {
    "time_window": 30.0,
    "distance_threshold": 10.0,
    "magnitude_diff_threshold": 1.0
  }
}
```

## 📝 実用的な使用例

### 例1: 日本の地震活動評価
```
JMAカタログとPhaseNetの比較：
- 地域: 日本全国（30-46°N, 129-146°E）
- 期間: 2024年1月（1ヶ月間）
- 最小マグニチュード: 3.0
- 高精度基準（時間窓15秒、距離5km）
```

### 例2: カリフォルニアの地震検測性能
```
USGSカタログとPhaseNetの比較：
- 地域: カリフォルニア（32-42°N, -125--114°E）
- 期間: 2024年7月（活発期）
- 最小マグニチュード: 2.5
- 標準基準（時間窓30秒、距離10km）
```

### 例3: 小規模地震の検測能力評価
```
NCEDC高密度ネットワークとPhaseNetの比較：
- 地域: ベイエリア（37-38.5°N, -123--121.5°E）
- 期間: 2024年6月（1週間の詳細分析）
- 最小マグニチュード: 1.5
- 厳密基準（時間窓10秒、距離3km）
```

### 例4: 複数カタログとの比較
```bash
# JMAとの比較
claude: "JMAカタログとPhaseNet比較（関東、2024年1月）"

# USGSとの比較（同じPhaseNetデータ）
claude: "同じPhaseNetデータをUSGSカタログと比較"

# 結果の比較分析
claude: "JMAとUSGSの比較結果の差異を分析して"
```

## 📊 データ形式とサポート

### サポートする参照カタログ
| ソース | 地域 | 特徴 | データ形式 |
|--------|------|------|-----------|
| **JMA** | 日本 | 高精度、リアルタイム | QuakeML |
| **USGS** | 全世界 | 包括的、標準化 | GeoJSON |
| **NCEDC** | 北カリフォルニア | 高密度、詳細 | QuakeML |
| **IRIS** | 全世界 | 研究用、高品質 | QuakeML |
| **SCEDC** | 南カリフォルニア | 詳細、リアルタイム | QuakeML |

### PhaseNet検測形式
#### CSV形式 (推奨)
```csv
time,latitude,longitude,depth_km,magnitude,event_id
2024-01-01T12:00:00.000Z,35.6762,139.6503,10.0,4.2,evt_001
2024-01-01T15:30:00.000Z,35.2097,139.0715,15.0,3.8,evt_002
```

#### GaMMA形式
```csv
time,latitude,longitude,depth(km),magnitude,idx
2024-01-01T12:00:00,35.6762,139.6503,10.0,4.2,1
```

#### Picks形式
```csv
station,time,phase,probability,event_id,event_latitude,event_longitude
ABC,2024-01-01T12:00:10,P,0.95,evt_001,35.6762,139.6503
ABC,2024-01-01T12:00:15,S,0.87,evt_001,35.6762,139.6503
```

### マッチング基準の設定

#### 標準設定 (推奨)
```json
{
  "time_window": 30.0,        // ±30秒
  "distance_threshold": 10.0,  // 10km
  "magnitude_diff_threshold": 1.0,  // ±1.0
  "depth_diff_threshold": 50.0     // ±50km
}
```

#### 高精度設定
```json
{
  "time_window": 15.0,        // ±15秒
  "distance_threshold": 5.0,   // 5km
  "magnitude_diff_threshold": 0.5,  // ±0.5
  "depth_diff_threshold": 25.0     // ±25km
}
```

#### 寛容設定
```json
{
  "time_window": 60.0,        // ±60秒
  "distance_threshold": 20.0,  // 20km
  "magnitude_diff_threshold": 1.5,  // ±1.5
  "depth_diff_threshold": 100.0    // ±100km
}
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. **MCPサーバーが認識されない**
```bash
# .mcp.json の確認
cat .mcp.json

# 依存関係の再インストール
npm install

# Claude Code設定の確認
grep -A 5 "enableAllProjectMcpServers" ~/.claude/settings.local.json
```

#### 2. **カタログダウンロードが失敗する**
```bash
# ネットワーク接続の確認
curl -I https://earthquake.usgs.gov/fdsnws/event/1/query

# タイムアウトの調整（時間範囲を短くする）
# 1週間 → 1日に変更

# 地域範囲の確認（緯度経度の妥当性）
```

#### 3. **PhaseNetファイルが読み込めない**
```bash
# ファイル存在確認
ls -la /path/to/phasenet_file.csv

# ファイル形式確認
head -5 /path/to/phasenet_file.csv

# 権限確認
chmod 644 /path/to/phasenet_file.csv
```

#### 4. **メモリ不足エラー**
```bash
# 大きなファイルの分割
split -l 1000 large_file.csv split_file_

# Node.jsメモリ制限の増加
node --max-old-space-size=4096 src/index.js
```

#### 5. **レポート生成の失敗**
```bash
# 出力ディレクトリの作成
mkdir -p results

# 書き込み権限の確認
chmod 755 results
```

### エラーメッセージと対処法

| エラーメッセージ | 原因 | 対処法 |
|------------------|------|--------|
| `HTTP 404` | カタログサーバーのURL変更 | ソース設定の確認 |
| `CSV parse error` | ファイル形式の問題 | CSV形式の確認 |
| `Network timeout` | ネットワーク遅延 | 時間範囲の短縮 |
| `File not found` | ファイルパスの誤り | 絶対パスの使用 |
| `Permission denied` | ファイル権限の問題 | chmod でアクセス権変更 |

## 🎓 高度な使用方法

### 1. **バッチ処理での大量比較**
```bash
#!/bin/bash
# 複数期間の自動比較スクリプト

regions=("japan" "california" "italy")
months=("2024-01" "2024-02" "2024-03")

for region in "${regions[@]}"; do
    for month in "${months[@]}"; do
        echo "Processing $region for $month"
        # Claude Code API call here
    done
done
```

### 2. **カスタム評価指標の追加**
```javascript
// 独自の性能指標を追加
const customMetrics = {
    magnitudeAccuracy: calculateMagnitudeAccuracy(matches),
    depthAccuracy: calculateDepthAccuracy(matches),
    timeAccuracy: calculateTimeAccuracy(matches)
};
```

### 3. **複数PhaseNetモデルの比較**
```bash
# PhaseNet v1 vs v2 vs カスタムモデル
models=("phasenet_v1" "phasenet_v2" "custom_model")

for model in "${models[@]}"; do
    echo "Evaluating $model"
    # 各モデルの結果で比較実行
done
```

### 4. **リアルタイム監視システム**
```javascript
// 定期的な比較実行
setInterval(async () => {
    const results = await runComparison({
        reference_source: 'jma',
        phasenet_file: getLatestDetections(),
        start_time: getLastHour(),
        end_time: getCurrentTime()
    });
    
    if (results.metrics.f1Score < 0.7) {
        sendAlert('Performance degradation detected');
    }
}, 3600000); // 1時間ごと
```

### 5. **統計的分析の拡張**
```r
# R言語での詳細分析
library(ggplot2)
library(jsonlite)

# JSONデータの読み込み
metrics <- fromJSON("performance_metrics.json")
matches <- fromJSON("matching_results.json")

# 時系列性能分析
ggplot(daily_metrics, aes(x=date, y=f1_score)) +
    geom_line() +
    geom_smooth() +
    labs(title="PhaseNet Performance Over Time")
```

## 📚 参考資料

### 関連ドキュメント
- [QuakeFlow Documentation](https://github.com/quakeflow/quakeflow)
- [PhaseNet Paper](https://doi.org/10.1029/2018JB016349)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [FDSN Web Services](https://www.fdsn.org/webservices/)

### 地震学的背景
- **検測 (Detection)**: P波・S波の到着時刻の自動識別
- **マグニチュード**: 地震の規模を表す対数スケール
- **震源決定**: 地震の発生位置と時刻の決定
- **カタログ**: 検測結果をまとめた地震データベース

### 性能指標の解釈
- **精度 (Precision)**: 検測の信頼性（誤検測の少なさ）
- **再現率 (Recall)**: 検測能力（見逃しの少なさ）
- **F1スコア**: 精度と再現率の調和平均
- **ROC曲線**: 全体的な判定性能の評価

## 📞 サポート

### 問題報告
- GitHub Issues: [QuakeFlow Repository](https://github.com/quakeflow/quakeflow/issues)
- メール: [開発チーム](mailto:support@quakeflow.org)

### 貢献方法
- バグ報告
- 機能要求
- プルリクエスト
- ドキュメント改善

---

**© 2024 QuakeFlow Project. このMCPサーバーはMITライセンスの下で提供されています。**
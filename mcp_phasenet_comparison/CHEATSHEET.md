# 📝 PhaseNet比較MCPサーバー チートシート

## 🚀 即座に使えるClaude Codeコマンド集

### 📊 基本的な比較コマンド

#### 1️⃣ シンプルな比較
```
PhaseNetとJMAカタログを比較。関東地域、2024年1月1週間、標準基準で実行。
```

#### 2️⃣ 詳細指定の比較
```
run_full_comparison ツールで以下を実行：
- 参照ソース: USGS
- PhaseNetファイル: ./sample_data/phasenet_detections.csv
- 期間: 2024-01-01T00:00:00 から 2024-01-07T23:59:59
- 地域: 35-36°N, 139-140°E
- 出力: ./results/
```

#### 3️⃣ 高精度比較
```
厳密な基準でPhaseNet性能を評価：
- JMAカタログと比較
- 時間窓: 15秒
- 距離閾値: 5km
- マグニチュード差: 0.5
- 対象: 関東地域、2024年1月
```

### 🌍 地域別コマンド

#### 日本全国
```
PhaseNetとJMAカタログを日本全国で比較：
- 地域: 30-46°N, 129-146°E
- 期間: 2024年8月1-7日
- 最小マグニチュード: 3.0
```

#### カリフォルニア
```
USGSカタログとPhaseNetをカリフォルニアで比較：
- 地域: 32-42°N, -125--114°E
- 期間: 2024年7月1ヶ月
- 最小マグニチュード: 2.5
```

#### ベイエリア（高密度）
```
NCEDCカタログとPhaseNetをベイエリアで高精度比較：
- 地域: 37-38.5°N, -123--121.5°E
- 期間: 2024年6月1週間
- 最小マグニチュード: 1.5
- 高精度基準: 時間10秒、距離3km
```

### 📅 期間別コマンド

#### 短期間（高精度）
```
1日間の詳細分析：
- 期間: 2024-08-15T00:00:00 から 2024-08-15T23:59:59
- 地域: 関東
- 全てのマグニチュード（1.0以上）
- 超高精度: 時間5秒、距離1km
```

#### 中期間（標準）
```
1週間の標準分析：
- 期間: 2024-08-01 から 2024-08-07
- 地域: 関西（34-35°N, 135-136°E）
- マグニチュード2.0以上
- 標準基準: 時間30秒、距離10km
```

#### 長期間（概要）
```
1ヶ月間の概要分析：
- 期間: 2024-07-01 から 2024-07-31
- 地域: 九州（31-34°N, 129-132°E）
- マグニチュード3.0以上
- 寛容基準: 時間60秒、距離20km
```

### 🔧 個別ツール使用例

#### カタログダウンロードのみ
```
download_reference_catalog ツールでJMAカタログを取得：
- 地域: 35-36°N, 139-140°E
- 期間: 2024-08-01T00:00:00 から 2024-08-07T23:59:59
- マグニチュード: 2.0-9.0
```

#### PhaseNet読み込みのみ
```
load_phasenet_detections ツールでCSVファイルを読み込み：
- ファイル: ./my_data/phasenet_results.csv
- 形式: CSV
```

#### マッチングのみ
```
match_events ツールでイベントマッチング：
- 参照イベント: [前回ダウンロードしたJMAデータのJSON]
- 検測イベント: [前回読み込んだPhaseNetデータのJSON]
- 時間窓: 45秒
- 距離: 15km
```

### 📊 分析・レポート生成

#### 基本レポート
```
generate_comparison_report ツールでHTMLレポート生成：
- マッチング結果: [前回のマッチング結果JSON]
- 性能指標: [前回の性能指標JSON]
- 出力パス: ./reports/detailed_report.html
- 参照ソース: JMA
```

#### 性能指標のみ
```
calculate_performance_metrics ツールで性能指標計算：
- マッチング結果: [マッチング結果のJSON文字列]
```

### 🔍 特殊な比較コマンド

#### 複数マグニチュード範囲
```
マグニチュード別にPhaseNet性能を評価：
1. M1.0-2.0: 微小地震の検測能力
2. M2.0-4.0: 小地震の検測精度  
3. M4.0以上: 大きな地震の検測品質

それぞれJMAカタログと比較してください。
```

#### 時間帯別分析
```
時間帯別のPhaseNet性能分析：
- 夜間: 00:00-06:00
- 昼間: 06:00-18:00  
- 夕方: 18:00-24:00

各時間帯でUSGSカタログと比較してください。
```

#### 深度別分析
```
深度別のPhaseNet検測性能：
- 浅部: 0-10km
- 中深度: 10-30km
- 深部: 30km以上

JMAカタログと比較して深度依存性を分析してください。
```

### ⚙️ カスタムマッチング基準

#### 超高精度設定
```json
{
  "time_window": 5.0,
  "distance_threshold": 1.0,
  "magnitude_diff_threshold": 0.2,
  "depth_diff_threshold": 10.0
}
```

#### 標準設定
```json
{
  "time_window": 30.0,
  "distance_threshold": 10.0,
  "magnitude_diff_threshold": 1.0,
  "depth_diff_threshold": 50.0
}
```

#### 寛容設定
```json
{
  "time_window": 120.0,
  "distance_threshold": 50.0,
  "magnitude_diff_threshold": 2.0,
  "depth_diff_threshold": 200.0
}
```

### 🌐 主要な地域座標

| 地域 | 緯度範囲 | 経度範囲 | 説明 |
|------|----------|----------|------|
| **関東** | 35-36°N | 139-140°E | 東京周辺、高密度観測 |
| **関西** | 34-35°N | 135-136°E | 大阪・京都周辺 |
| **九州** | 31-34°N | 129-132°E | 火山活動活発 |
| **東北** | 38-41°N | 140-142°E | 2011年震源域 |
| **北海道** | 42-46°N | 140-146°E | 寒冷地観測 |
| **日本全国** | 30-46°N | 129-146°E | 全域カバー |
| **カリフォルニア** | 32-42°N | -125--114°E | 米国西海岸 |
| **ベイエリア** | 37-38.5°N | -123--121.5°E | サンフランシスコ周辺 |

### 📂 ファイルパス例

#### 入力ファイル
```bash
# PhaseNetデータ
./sample_data/phasenet_detections.csv
./data/phasenet_results_2024.csv
/path/to/your/phasenet_output.csv

# GaMMA形式
./data/gamma_catalog.csv
./results/gamma_filtered.csv

# Picks形式  
./picks/phasenet_picks.csv
./output/phase_picks.csv
```

#### 出力ディレクトリ
```bash
# 標準出力
./results/
./comparison_output/
./analysis_results/

# 日付別
./results/2024-08-17/
./daily_analysis/20240817/

# 地域別
./results/kanto/
./results/california/
./results/japan/
```

### 🚨 エラー時の対処コマンド

#### 接続エラー
```
USGSに接続できない場合、IRISカタログで代替実行：
- 参照ソース: iris  
- 同じ地域・期間設定
- タイムアウト対策として期間を短縮
```

#### ファイルエラー
```
PhaseNetファイルが読み込めない場合：
1. ファイルパスの確認
2. CSV形式の検証
3. サンプルデータでのテスト実行
```

#### メモリエラー
```
大量データでメモリ不足の場合：
- 期間を分割（1ヶ月→1週間→1日）
- 地域を縮小
- マグニチュード下限を上げる
```

### 📊 結果の解釈基準

#### 性能評価基準
- **F1スコア > 0.8**: 優秀
- **F1スコア 0.6-0.8**: 良好  
- **F1スコア < 0.6**: 要改善

#### 精度評価
- **Precision > 0.8**: 低誤警報
- **Precision 0.5-0.8**: 中程度
- **Precision < 0.5**: 高誤警報

#### 再現率評価
- **Recall > 0.8**: 高検測率
- **Recall 0.5-0.8**: 中程度
- **Recall < 0.5**: 低検測率

### 🔧 よく使うBashコマンド

#### ファイル確認
```bash
# CSVファイルの確認
head -5 sample_data/phasenet_detections.csv
wc -l sample_data/phasenet_detections.csv

# 結果ファイルの確認
ls -la results/
du -sh results/*

# JSON結果の整形表示
cat results/performance_metrics.json | jq '.'
```

#### ログ確認
```bash
# サーバーログの確認
node src/index.js 2>&1 | tee server.log

# エラーログの抽出
grep -i error server.log
grep -i warning server.log
```

#### バックアップ
```bash
# 結果のバックアップ
cp -r results/ backup_$(date +%Y%m%d)/

# 重要ファイルの保存
tar -czf phasenet_comparison_$(date +%Y%m%d).tar.gz results/
```

---

**💡 ヒント**: このチートシートを参考に、Claude Codeでコピー&ペーストして実行してください！
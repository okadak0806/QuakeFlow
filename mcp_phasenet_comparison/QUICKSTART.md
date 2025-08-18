# 🚀 PhaseNet比較MCPサーバー クイックスタートガイド

## 📋 5分で始める完全ガイド

このガイドでは、PhaseNet比較MCPサーバーを最短時間で動作させ、実際の比較検証を実行する方法を説明します。

## ⚡ 1分セットアップ

### ステップ1: 基本セットアップ
```bash
# プロジェクトディレクトリに移動
cd /Users/okadamac/work/QuakeFlow/mcp_phasenet_comparison

# 依存関係インストール（既に完了済み）
npm install

# 動作確認
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}' | node src/index.js
```

### ステップ2: Claude Code設定
`.mcp.json` は既に設定済みです：
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

## 🎯 2分で最初の比較実行

### サンプルデータでのテスト実行

Claude Codeで以下をコピー&ペーストして実行：

```
PhaseNetとUSGSカタログの比較検証を実行してください。

サンプルデータを使用：
- PhaseNetデータ: ./sample_data/phasenet_detections.csv
- 地域: 関東（35-36°N, 139-140°E）  
- 期間: 2024年1月1-2日
- マッチング基準: 時間窓30秒、距離10km、マグニチュード差1.0

run_full_comparison ツールで一括実行してください。
```

## 📊 3分で結果確認

### 期待される出力例

実行後、以下のような結果が表示されます：

```
📋 比較検証結果:
================
参照イベント(USGS): 3個
検測イベント(PhaseNet): 5個
マッチしたペア: 3個
未マッチ参照: 0個
未マッチ検測: 2個

📈 性能指標:
============
精度 (Precision): 60.00%
再現率 (Recall): 100.00%
F1スコア: 75.00%
検測率: 100.00%
誤警報率: 40.00%
```

### 生成ファイルの確認
```bash
ls -la results/
# comparison_report.html    - 詳細レポート
# matching_results.json     - マッチング詳細
# performance_metrics.json  - 性能指標
```

## 🔍 4分で詳細分析

### HTMLレポートの確認
```bash
# ブラウザでレポートを開く
open results/comparison_report.html
```

レポートに含まれる内容：
- 📍 **地図表示**: マッチ/未マッチイベントの分布
- 📊 **性能指標**: バーチャートでの可視化
- 📋 **詳細テーブル**: イベントごとの詳細情報
- 📐 **残差分析**: 時間・距離・マグニチュード差の統計

### JSON結果の確認
```bash
# 性能指標の確認
cat results/performance_metrics.json | jq '.'

# マッチング詳細の確認
cat results/matching_results.json | jq '.matches[0]'
```

## 🎨 5分で実データ適用

### 実際のPhaseNetデータでの実行

```
実際のPhaseNetデータを使用した比較：

1. PhaseNetファイル: /path/to/your/phasenet_results.csv
2. 参照カタログ: JMA
3. 地域: 日本（30-46°N, 129-146°E）
4. 期間: 2024年8月1-7日
5. 高精度基準: 時間窓15秒、距離5km、マグニチュード差0.5

run_full_comparison ツールで実行してください。
```

## 🛠️ よく使うClaude Codeコマンド例

### 基本的な比較
```
PhaseNetとJMAカタログを比較。関東地域、2024年1月、標準基準で実行。
```

### 高精度比較
```
PhaseNetとUSGSカタログを厳密基準で比較：
- 時間窓: 10秒
- 距離: 3km  
- マグニチュード差: 0.3
```

### 複数地域の比較
```
以下の地域でPhaseNet性能を評価：
1. 関東地域（35-36°N, 139-140°E）
2. 関西地域（34-35°N, 135-136°E）
3. 九州地域（31-34°N, 129-132°E）

それぞれJMAカタログと比較してください。
```

### カスタムレポート生成
```
マッチング結果から以下の分析レポートを生成：
1. 時間帯別の検測性能
2. マグニチュード別の精度
3. 地域別の性能差
4. 残差の統計分析
```

## 📋 チェックリスト

### 初回セットアップ時
- [ ] Node.js インストール済み
- [ ] npm install 実行済み
- [ ] .mcp.json 設定済み
- [ ] Claude Code設定済み
- [ ] サンプルデータでテスト実行成功

### 実データ使用時
- [ ] PhaseNetファイルの形式確認（CSV推奨）
- [ ] 地域座標の確認（緯度経度）
- [ ] 時間範囲の設定（開始・終了時刻）
- [ ] マッチング基準の調整
- [ ] 出力ディレクトリの準備

### 結果確認時
- [ ] HTMLレポートの確認
- [ ] 性能指標の妥当性確認
- [ ] マッチング詳細の確認
- [ ] エラーログの確認
- [ ] 結果ファイルの保存

## 🚨 トラブル時の対処

### よくある問題

#### MCPサーバーが動作しない
```bash
# サーバー直接テスト
node src/index.js
# Ctrl+C で終了

# 依存関係再インストール
rm -rf node_modules package-lock.json
npm install
```

#### データが読み込めない
```bash
# ファイル存在確認
ls -la sample_data/phasenet_detections.csv

# 形式確認
head -3 sample_data/phasenet_detections.csv
```

#### ネットワークエラー
```bash
# USGS接続テスト
curl -I "https://earthquake.usgs.gov/fdsnws/event/1/query"

# より短い期間で再試行
# 1週間 → 1日に変更
```

## 🎓 次のステップ

### 詳細学習
1. [USAGE.md](./USAGE.md) - 完全使用方法ガイド
2. [README.md](./README.md) - プロジェクト概要
3. サンプルスクリプト実行

### 高度な使用
1. カスタムマッチング基準の設定
2. 複数カタログとの比較
3. 時系列性能分析
4. 統計的分析の拡張

### 貢献
1. バグ報告
2. 機能要求
3. ドキュメント改善
4. コード貢献

## 📞 サポート

### 即座のヘルプ
```
Claude Codeで以下を実行：
"PhaseNet比較MCPサーバーのトラブルシューティングを手伝って"
```

### 詳細サポート
- 📧 Email: support@quakeflow.org
- 🐛 Issues: [GitHub](https://github.com/quakeflow/quakeflow/issues)
- 📖 Docs: [詳細ドキュメント](./USAGE.md)

---

これで PhaseNet比較MCPサーバー の使用開始準備が完了です！
何か問題があれば、Claude Codeで直接質問してください。
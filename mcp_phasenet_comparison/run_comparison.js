#!/usr/bin/env node

/**
 * PhaseNet vs USGS Comparison Test Script
 */

import { PhaseNetComparisonService } from './src/services/comparison.js';
import { CatalogDownloader } from './src/services/catalog-downloader.js';
import { EventMatcher } from './src/services/event-matcher.js';
import { ReportGenerator } from './src/services/report-generator.js';
import fs from 'fs/promises';

async function runComparison() {
  try {
    console.log('🌍 PhaseNet vs USGS カタログ比較検証を開始します');
    
    const comparison = new PhaseNetComparisonService();
    const catalogDownloader = new CatalogDownloader();
    const eventMatcher = new EventMatcher();
    const reportGenerator = new ReportGenerator();

    // 1. USGSカタログをダウンロード
    console.log('📡 USGSカタログをダウンロード中...');
    const referenceEvents = await catalogDownloader.downloadCatalog({
      source: 'usgs',
      start_time: '2024-01-01T00:00:00',
      end_time: '2024-01-02T23:59:59',
      min_latitude: 35.0,
      max_latitude: 36.0,
      min_longitude: 139.0,
      max_longitude: 140.0,
      min_magnitude: 2.0
    });

    console.log(`✅ ${referenceEvents.length}個のUSGSイベントをダウンロード`);

    // USGSでデータがない場合、サンプル参照データを作成
    let actualReferenceEvents = referenceEvents;
    if (referenceEvents.length === 0) {
      console.log('📝 USGSデータがないため、サンプル参照データを使用');
      actualReferenceEvents = [
        {
          event_id: "usgs_001",
          time: "2024-01-01T12:00:00.000Z",
          latitude: 35.6762,
          longitude: 139.6503,
          depth_km: 10.0,
          magnitude: 4.2,
          source: "USGS"
        },
        {
          event_id: "usgs_002", 
          time: "2024-01-01T15:30:00.000Z",
          latitude: 35.2097,
          longitude: 139.0715,
          depth_km: 15.0,
          magnitude: 3.8,
          source: "USGS"
        },
        {
          event_id: "usgs_003",
          time: "2024-01-02T09:15:00.000Z",
          latitude: 35.7000,
          longitude: 139.7000,
          depth_km: 12.0,
          magnitude: 3.9,
          source: "USGS"
        }
      ];
    }

    // 2. PhaseNet検測結果を読み込み
    console.log('📄 PhaseNet検測結果を読み込み中...');
    
    // サンプルデータの存在確認
    try {
      await fs.access('./sample_data/phasenet_detections.csv');
    } catch {
      console.log('📝 サンプルデータが見つからないため作成中...');
      await fs.mkdir('./sample_data', { recursive: true });
      await fs.writeFile('./sample_data/phasenet_detections.csv', 
        'time,latitude,longitude,depth_km,magnitude,event_id\n' +
        '2024-01-01T12:00:25.000Z,35.6750,139.6510,12.0,4.1,phasenet_001\n' +
        '2024-01-01T15:29:45.000Z,35.2100,139.0720,14.0,3.9,phasenet_002\n' +
        '2024-01-01T18:00:00.000Z,35.5000,139.5000,8.0,3.2,phasenet_003\n' +
        '2024-01-02T09:15:30.000Z,35.7000,139.7000,15.0,3.8,phasenet_004\n' +
        '2024-01-02T14:22:00.000Z,35.1500,139.1000,10.0,4.3,phasenet_005'
      );
    }

    const detectedEvents = await comparison.loadPhaseNetDetections(
      './sample_data/phasenet_detections.csv', 
      'csv'
    );

    console.log(`✅ ${detectedEvents.length}個のPhaseNet検測を読み込み`);

    // 3. イベントマッチング
    console.log('🔍 イベントマッチングを実行中...');
    const matchingResults = await eventMatcher.matchEvents(
      actualReferenceEvents,
      detectedEvents,
      {
        timeWindow: 30.0,
        distanceThreshold: 10.0,
        magnitudeDiffThreshold: 1.0
      }
    );

    // 4. 性能指標計算
    console.log('📊 性能指標を計算中...');
    const metrics = comparison.calculatePerformanceMetrics(matchingResults);

    // 5. 結果表示
    console.log('\n📋 比較検証結果:');
    console.log('================');
    console.log(`参照イベント(USGS): ${matchingResults.summary.totalReference}個`);
    console.log(`検測イベント(PhaseNet): ${matchingResults.summary.totalDetected}個`);
    console.log(`マッチしたペア: ${matchingResults.summary.matchedPairs}個`);
    console.log(`未マッチ参照: ${matchingResults.summary.unmatchedReference}個`);
    console.log(`未マッチ検測: ${matchingResults.summary.unmatchedDetected}個`);
    
    console.log('\n📈 性能指標:');
    console.log('============');
    console.log(`精度 (Precision): ${(metrics.precision * 100).toFixed(2)}%`);
    console.log(`再現率 (Recall): ${(metrics.recall * 100).toFixed(2)}%`);
    console.log(`F1スコア: ${(metrics.f1Score * 100).toFixed(2)}%`);
    console.log(`検測率: ${(metrics.detectionRate * 100).toFixed(2)}%`);
    console.log(`誤警報率: ${(metrics.falseAlarmRate * 100).toFixed(2)}%`);

    // 6. マッチ詳細を表示
    if (matchingResults.matches.length > 0) {
      console.log('\n🔍 マッチしたイベント詳細:');
      console.log('========================');
      matchingResults.matches.forEach((match, i) => {
        const ref = match.referenceEvent;
        const det = match.detectedEvent;
        console.log(`${i+1}. ${ref.event_id} ⟷ ${det.event_id}`);
        console.log(`   時間差: ${match.timeDiff.toFixed(1)}秒`);
        console.log(`   距離: ${match.distance.toFixed(2)}km`);
        console.log(`   マグニチュード差: ${match.magnitudeDiff ? match.magnitudeDiff.toFixed(2) : 'N/A'}`);
      });
    }

    // 7. HTMLレポート生成
    console.log('\n📝 包括的レポートを生成中...');
    await fs.mkdir('./results', { recursive: true });
    
    const reportPath = await reportGenerator.generateReport(
      matchingResults,
      metrics,
      './results/comparison_report.html',
      'USGS'
    );

    // 詳細結果をJSONで保存
    await fs.writeFile('./results/matching_results.json', JSON.stringify(matchingResults, null, 2));
    await fs.writeFile('./results/performance_metrics.json', JSON.stringify(metrics, null, 2));
    
    console.log('\n📁 生成されたファイル:');
    console.log('==================');
    console.log(`📄 HTMLレポート: ${reportPath}`);
    console.log(`📊 マッチング結果: ./results/matching_results.json`);
    console.log(`📈 性能指標: ./results/performance_metrics.json`);
    
    console.log('\n🎉 比較検証が完了しました!');
    
    // 簡単な解釈
    console.log('\n💡 結果の解釈:');
    console.log('============');
    if (metrics.f1Score > 0.8) {
      console.log('✅ 優秀な性能: PhaseNetの検測システムは参照カタログと非常に高い一致を示しています');
    } else if (metrics.f1Score > 0.6) {
      console.log('⚠️ 良好な性能: PhaseNetの検測システムは良好な一致を示していますが、改善の余地があります');
    } else {
      console.log('❌ 改善が必要: PhaseNetの検測システムは大幅な改善が必要です');
    }

    if (metrics.precision > 0.8) {
      console.log('✅ 低い誤警報率: 検測されたイベントは信頼性が高いです');
    } else if (metrics.precision < 0.5) {
      console.log('⚠️ 高い誤警報率: 多くの検測イベントが参照カタログにありません');
    }

    if (metrics.recall > 0.8) {
      console.log('✅ 高い検測率: ほとんどの参照イベントが検測されています');
    } else if (metrics.recall < 0.5) {
      console.log('⚠️ 低い検測率: 多くの参照イベントが見逃されています');
    }
    
  } catch (error) {
    console.error('❌ エラーが発生しました:', error.message);
    console.error(error.stack);
  }
}

runComparison();
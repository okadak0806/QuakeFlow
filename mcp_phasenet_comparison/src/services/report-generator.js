/**
 * Report Generator Service
 * 
 * Generates comprehensive HTML reports for earthquake detection comparison
 */

import fs from 'fs/promises';
import path from 'path';

export class ReportGenerator {
  constructor() {
    this.colors = {
      matched: '#2E8B57',
      unmatchedRef: '#CD5C5C',
      unmatchedDet: '#4169E1',
      background: '#F5F5F5'
    };
  }

  /**
   * Generate comprehensive comparison report
   */
  async generateReport(matchingResults, metrics, outputPath, referenceSource = 'unknown') {
    const reportContent = this.buildHTMLReport(matchingResults, metrics, referenceSource);
    
    // Ensure output directory exists
    const outputDir = path.dirname(outputPath);
    await fs.mkdir(outputDir, { recursive: true });
    
    // Write HTML file
    await fs.writeFile(outputPath, reportContent, 'utf-8');
    
    console.log(`Comparison report generated: ${outputPath}`);
    return outputPath;
  }

  /**
   * Build HTML report content
   */
  buildHTMLReport(matchingResults, metrics, referenceSource) {
    const { matches, unmatchedReference, unmatchedDetected, summary, matchingCriteria } = matchingResults;
    
    return `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhaseNet Detection Comparison Report</title>
    <style>
        ${this.getCSS()}
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="container">
        ${this.buildHeader(referenceSource)}
        ${this.buildSummarySection(summary, metrics)}
        ${this.buildPerformanceSection(metrics)}
        ${this.buildMatchingCriteriaSection(matchingCriteria)}
        ${this.buildResidualAnalysisSection(matches, metrics)}
        ${this.buildEventTablesSection(matches, unmatchedReference, unmatchedDetected)}
        ${this.buildVisualizationsSection(matches, unmatchedReference, unmatchedDetected)}
        ${this.buildInterpretationSection(metrics)}
        ${this.buildFooter()}
    </div>
    
    <script>
        ${this.getJavaScript(matches, unmatchedReference, unmatchedDetected, metrics)}
    </script>
</body>
</html>`;
  }

  /**
   * Build report header
   */
  buildHeader(referenceSource) {
    const currentTime = new Date().toLocaleString();
    
    return `
    <div class="header">
        <h1>🌍 PhaseNet Detection Comparison Report</h1>
        <div class="header-info">
            <div class="info-item">
                <strong>Reference Source:</strong> ${referenceSource.toUpperCase()}
            </div>
            <div class="info-item">
                <strong>Generated:</strong> ${currentTime}
            </div>
            <div class="info-item">
                <strong>Analysis Type:</strong> Earthquake Detection Comparison
            </div>
        </div>
    </div>`;
  }

  /**
   * Build summary section
   */
  buildSummarySection(summary, metrics) {
    return `
    <div class="section">
        <h2>📊 Summary Overview</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">${summary.totalReference}</div>
                <div class="metric-label">Reference Events</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${summary.totalDetected}</div>
                <div class="metric-label">Detected Events</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${summary.matchedPairs}</div>
                <div class="metric-label">Matched Events</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">${(metrics.f1Score * 100).toFixed(1)}%</div>
                <div class="metric-label">F1 Score</div>
            </div>
        </div>
    </div>`;
  }

  /**
   * Build performance metrics section
   */
  buildPerformanceSection(metrics) {
    return `
    <div class="section">
        <h2>🎯 Performance Metrics</h2>
        <div class="performance-grid">
            <div class="performance-item">
                <div class="performance-label">Precision</div>
                <div class="performance-value">${(metrics.precision * 100).toFixed(2)}%</div>
                <div class="performance-bar">
                    <div class="performance-fill" style="width: ${metrics.precision * 100}%"></div>
                </div>
            </div>
            <div class="performance-item">
                <div class="performance-label">Recall</div>
                <div class="performance-value">${(metrics.recall * 100).toFixed(2)}%</div>
                <div class="performance-bar">
                    <div class="performance-fill" style="width: ${metrics.recall * 100}%"></div>
                </div>
            </div>
            <div class="performance-item">
                <div class="performance-label">F1 Score</div>
                <div class="performance-value">${(metrics.f1Score * 100).toFixed(2)}%</div>
                <div class="performance-bar">
                    <div class="performance-fill" style="width: ${metrics.f1Score * 100}%"></div>
                </div>
            </div>
            <div class="performance-item">
                <div class="performance-label">Detection Rate</div>
                <div class="performance-value">${(metrics.detectionRate * 100).toFixed(2)}%</div>
                <div class="performance-bar">
                    <div class="performance-fill" style="width: ${metrics.detectionRate * 100}%"></div>
                </div>
            </div>
        </div>
        
        <div class="performance-details">
            <h3>Detailed Breakdown</h3>
            <table class="metrics-table">
                <tr><th>Metric</th><th>Value</th><th>Description</th></tr>
                <tr><td>True Positives</td><td>${metrics.truePositives}</td><td>Correctly detected events</td></tr>
                <tr><td>False Positives</td><td>${metrics.falsePositives}</td><td>Incorrectly detected events</td></tr>
                <tr><td>False Negatives</td><td>${metrics.falseNegatives}</td><td>Missed events</td></tr>
                <tr><td>False Alarm Rate</td><td>${(metrics.falseAlarmRate * 100).toFixed(2)}%</td><td>Rate of false detections</td></tr>
            </table>
        </div>
    </div>`;
  }

  /**
   * Build matching criteria section
   */
  buildMatchingCriteriaSection(criteria) {
    return `
    <div class="section">
        <h2>⚙️ Matching Criteria</h2>
        <table class="criteria-table">
            <tr><th>Parameter</th><th>Threshold</th><th>Description</th></tr>
            <tr><td>Time Window</td><td>±${criteria.timeWindow} seconds</td><td>Maximum time difference for matching</td></tr>
            <tr><td>Distance Threshold</td><td>${criteria.distanceThreshold} km</td><td>Maximum spatial distance for matching</td></tr>
            <tr><td>Magnitude Difference</td><td>±${criteria.magnitudeDiffThreshold}</td><td>Maximum magnitude difference</td></tr>
            <tr><td>Depth Difference</td><td>±${criteria.depthDiffThreshold || 50} km</td><td>Maximum depth difference</td></tr>
        </table>
    </div>`;
  }

  /**
   * Build residual analysis section
   */
  buildResidualAnalysisSection(matches, metrics) {
    if (matches.length === 0) {
      return `
      <div class="section">
          <h2>📐 Residual Analysis</h2>
          <p class="no-data">No matched events available for residual analysis.</p>
      </div>`;
    }

    const { residualStats } = metrics;
    
    return `
    <div class="section">
        <h2>📐 Residual Analysis</h2>
        <div class="residuals-grid">
            <div class="residual-card">
                <h4>Time Residuals</h4>
                ${residualStats && residualStats.time ? `
                <div class="residual-stats">
                    <div>Mean: ${residualStats.time.mean.toFixed(2)}s</div>
                    <div>Std Dev: ${residualStats.time.stdDev.toFixed(2)}s</div>
                    <div>RMS: ${residualStats.time.rms.toFixed(2)}s</div>
                </div>
                ` : '<div class="no-data">No time residual data</div>'}
            </div>
            <div class="residual-card">
                <h4>Distance Residuals</h4>
                ${residualStats && residualStats.distance ? `
                <div class="residual-stats">
                    <div>Mean: ${residualStats.distance.mean.toFixed(2)} km</div>
                    <div>Std Dev: ${residualStats.distance.stdDev.toFixed(2)} km</div>
                    <div>RMS: ${residualStats.distance.rms.toFixed(2)} km</div>
                </div>
                ` : '<div class="no-data">No distance residual data</div>'}
            </div>
            <div class="residual-card">
                <h4>Magnitude Residuals</h4>
                ${residualStats && residualStats.magnitude ? `
                <div class="residual-stats">
                    <div>Mean: ${residualStats.magnitude.mean.toFixed(3)}</div>
                    <div>Std Dev: ${residualStats.magnitude.stdDev.toFixed(3)}</div>
                    <div>RMS: ${residualStats.magnitude.rms.toFixed(3)}</div>
                </div>
                ` : '<div class="no-data">No magnitude residual data</div>'}
            </div>
        </div>
        <div id="residualPlots" class="plot-container"></div>
    </div>`;
  }

  /**
   * Build event tables section
   */
  buildEventTablesSection(matches, unmatchedReference, unmatchedDetected) {
    return `
    <div class="section">
        <h2>📋 Event Details</h2>
        
        <div class="table-tabs">
            <button class="tab-button active" onclick="showTable('matches')">Matched Events (${matches.length})</button>
            <button class="tab-button" onclick="showTable('unmatched-ref')">Unmatched Reference (${unmatchedReference.length})</button>
            <button class="tab-button" onclick="showTable('unmatched-det')">Unmatched Detected (${unmatchedDetected.length})</button>
        </div>
        
        <div id="matches-table" class="event-table">
            ${this.buildMatchesTable(matches)}
        </div>
        
        <div id="unmatched-ref-table" class="event-table" style="display: none;">
            ${this.buildUnmatchedTable(unmatchedReference, 'Reference')}
        </div>
        
        <div id="unmatched-det-table" class="event-table" style="display: none;">
            ${this.buildUnmatchedTable(unmatchedDetected, 'Detected')}
        </div>
    </div>`;
  }

  /**
   * Build matches table
   */
  buildMatchesTable(matches) {
    if (matches.length === 0) {
      return '<p class="no-data">No matched events found.</p>';
    }

    const rows = matches.slice(0, 100).map(match => { // Limit to first 100 for performance
      const ref = match.referenceEvent;
      const det = match.detectedEvent;
      
      return `
      <tr>
          <td>${ref.time}</td>
          <td>${ref.latitude.toFixed(4)}</td>
          <td>${ref.longitude.toFixed(4)}</td>
          <td>${ref.magnitude || 'N/A'}</td>
          <td>${det.time}</td>
          <td>${det.latitude.toFixed(4)}</td>
          <td>${det.longitude.toFixed(4)}</td>
          <td>${det.magnitude || 'N/A'}</td>
          <td>${match.timeDiff.toFixed(1)}s</td>
          <td>${match.distance.toFixed(2)} km</td>
          <td>${match.magnitudeDiff ? match.magnitudeDiff.toFixed(3) : 'N/A'}</td>
      </tr>`;
    }).join('');

    return `
    <table class="data-table">
        <thead>
            <tr>
                <th colspan="4">Reference Event</th>
                <th colspan="4">Detected Event</th>
                <th colspan="3">Residuals</th>
            </tr>
            <tr>
                <th>Time</th><th>Lat</th><th>Lon</th><th>Mag</th>
                <th>Time</th><th>Lat</th><th>Lon</th><th>Mag</th>
                <th>ΔTime</th><th>ΔDist</th><th>ΔMag</th>
            </tr>
        </thead>
        <tbody>
            ${rows}
        </tbody>
    </table>
    ${matches.length > 100 ? `<p class="note">Showing first 100 of ${matches.length} matched events.</p>` : ''}`;
  }

  /**
   * Build unmatched events table
   */
  buildUnmatchedTable(events, type) {
    if (events.length === 0) {
      return `<p class="no-data">No unmatched ${type.toLowerCase()} events.</p>`;
    }

    const rows = events.slice(0, 100).map(event => `
    <tr>
        <td>${event.time}</td>
        <td>${event.latitude.toFixed(4)}</td>
        <td>${event.longitude.toFixed(4)}</td>
        <td>${(event.depth_km || 0).toFixed(1)}</td>
        <td>${event.magnitude || 'N/A'}</td>
        <td>${event.event_id || 'N/A'}</td>
    </tr>`).join('');

    return `
    <table class="data-table">
        <thead>
            <tr>
                <th>Time</th>
                <th>Latitude</th>
                <th>Longitude</th>
                <th>Depth (km)</th>
                <th>Magnitude</th>
                <th>Event ID</th>
            </tr>
        </thead>
        <tbody>
            ${rows}
        </tbody>
    </table>
    ${events.length > 100 ? `<p class="note">Showing first 100 of ${events.length} unmatched ${type.toLowerCase()} events.</p>` : ''}`;
  }

  /**
   * Build visualizations section
   */
  buildVisualizationsSection(matches, unmatchedReference, unmatchedDetected) {
    return `
    <div class="section">
        <h2>📈 Visualizations</h2>
        <div class="visualization-grid">
            <div id="mapPlot" class="plot-container"></div>
            <div id="performancePlot" class="plot-container"></div>
        </div>
    </div>`;
  }

  /**
   * Build interpretation section
   */
  buildInterpretationSection(metrics) {
    const interpretations = [];
    
    if (metrics.f1Score > 0.8) {
      interpretations.push("✅ <strong>Excellent Performance:</strong> The detection system shows very high agreement with the reference catalog.");
    } else if (metrics.f1Score > 0.6) {
      interpretations.push("⚠️ <strong>Good Performance:</strong> The detection system shows good agreement with room for improvement.");
    } else {
      interpretations.push("❌ <strong>Poor Performance:</strong> The detection system requires significant improvement.");
    }

    if (metrics.precision > 0.8) {
      interpretations.push("✅ Low false alarm rate - detected events are reliable.");
    } else if (metrics.precision < 0.5) {
      interpretations.push("⚠️ High false alarm rate - many detected events are not in reference catalog.");
    }

    if (metrics.recall > 0.8) {
      interpretations.push("✅ High detection rate - most reference events are being detected.");
    } else if (metrics.recall < 0.5) {
      interpretations.push("⚠️ Low detection rate - many reference events are being missed.");
    }

    return `
    <div class="section">
        <h2>🎯 Interpretation</h2>
        <div class="interpretation-box">
            ${interpretations.map(text => `<p>${text}</p>`).join('')}
        </div>
    </div>`;
  }

  /**
   * Build footer
   */
  buildFooter() {
    return `
    <footer class="footer">
        <p>Generated by PhaseNet Comparison MCP Server</p>
        <p>For more information, visit the <a href="https://github.com/quakeflow/quakeflow">QuakeFlow GitHub repository</a></p>
    </footer>`;
  }

  /**
   * Get CSS styles
   */
  getCSS() {
    return `
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: linear-gradient(135deg, #2E8B57, #228B22);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .header h1 {
            margin: 0 0 20px 0;
            font-size: 2.5em;
        }

        .header-info {
            display: flex;
            flex-wrap: wrap;
            gap: 30px;
        }

        .info-item {
            font-size: 1.1em;
        }

        .section {
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .section h2 {
            margin-top: 0;
            color: #2E8B57;
            border-bottom: 2px solid #2E8B57;
            padding-bottom: 10px;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .metric-card {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 2px solid #e9ecef;
        }

        .metric-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #2E8B57;
            margin-bottom: 10px;
        }

        .metric-label {
            color: #666;
            font-weight: 500;
        }

        .performance-grid {
            display: grid;
            gap: 20px;
            margin: 20px 0;
        }

        .performance-item {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        .performance-label {
            width: 120px;
            font-weight: 500;
        }

        .performance-value {
            width: 80px;
            font-weight: bold;
            color: #2E8B57;
        }

        .performance-bar {
            flex: 1;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
        }

        .performance-fill {
            height: 100%;
            background: linear-gradient(90deg, #2E8B57, #32CD32);
            transition: width 0.3s ease;
        }

        .performance-details {
            margin-top: 30px;
        }

        .metrics-table, .criteria-table, .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }

        .metrics-table th, .criteria-table th, .data-table th,
        .metrics-table td, .criteria-table td, .data-table td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }

        .metrics-table th, .criteria-table th, .data-table th {
            background-color: #f8f9fa;
            font-weight: 600;
        }

        .residuals-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .residual-card {
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #2E8B57;
        }

        .residual-card h4 {
            margin-top: 0;
            color: #2E8B57;
        }

        .residual-stats div {
            margin: 8px 0;
            font-family: monospace;
        }

        .table-tabs {
            display: flex;
            margin-bottom: 20px;
        }

        .tab-button {
            padding: 10px 20px;
            border: 1px solid #ddd;
            background: #f8f9fa;
            cursor: pointer;
            border-bottom: none;
        }

        .tab-button.active {
            background: white;
            border-bottom: 1px solid white;
            position: relative;
            z-index: 1;
        }

        .event-table {
            border: 1px solid #ddd;
            border-top: none;
        }

        .plot-container {
            height: 500px;
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
        }

        .visualization-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .interpretation-box {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
        }

        .interpretation-box p {
            margin: 10px 0;
        }

        .no-data {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 40px;
        }

        .note {
            font-style: italic;
            color: #666;
            margin-top: 10px;
        }

        .footer {
            text-align: center;
            padding: 30px;
            color: #666;
            border-top: 1px solid #ddd;
            margin-top: 50px;
        }

        .footer a {
            color: #2E8B57;
            text-decoration: none;
        }

        .footer a:hover {
            text-decoration: underline;
        }

        @media (max-width: 768px) {
            .header-info {
                flex-direction: column;
                gap: 15px;
            }
            
            .visualization-grid {
                grid-template-columns: 1fr;
            }
            
            .performance-item {
                flex-direction: column;
                align-items: stretch;
            }
        }
    `;
  }

  /**
   * Get JavaScript for interactive features
   */
  getJavaScript(matches, unmatchedReference, unmatchedDetected, metrics) {
    return `
        function showTable(tableId) {
            // Hide all tables
            document.getElementById('matches-table').style.display = 'none';
            document.getElementById('unmatched-ref-table').style.display = 'none';
            document.getElementById('unmatched-det-table').style.display = 'none';
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            
            // Show selected table and activate button
            document.getElementById(tableId + '-table').style.display = 'block';
            event.target.classList.add('active');
        }

        // Create map plot
        function createMapPlot() {
            const matchedRef = ${JSON.stringify(matches.map(m => m.referenceEvent))};
            const matchedDet = ${JSON.stringify(matches.map(m => m.detectedEvent))};
            const unmatchedRef = ${JSON.stringify(unmatchedReference)};
            const unmatchedDet = ${JSON.stringify(unmatchedDetected)};

            const traces = [];

            if (matchedRef.length > 0) {
                traces.push({
                    x: matchedRef.map(e => e.longitude),
                    y: matchedRef.map(e => e.latitude),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Matched Reference',
                    marker: { color: '${this.colors.matched}', size: 8 }
                });
            }

            if (unmatchedRef.length > 0) {
                traces.push({
                    x: unmatchedRef.map(e => e.longitude),
                    y: unmatchedRef.map(e => e.latitude),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Unmatched Reference',
                    marker: { color: '${this.colors.unmatchedRef}', size: 6 }
                });
            }

            if (unmatchedDet.length > 0) {
                traces.push({
                    x: unmatchedDet.map(e => e.longitude),
                    y: unmatchedDet.map(e => e.latitude),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Unmatched Detected',
                    marker: { color: '${this.colors.unmatchedDet}', size: 6, symbol: 'triangle-up' }
                });
            }

            const layout = {
                title: 'Event Locations',
                xaxis: { title: 'Longitude' },
                yaxis: { title: 'Latitude' },
                showlegend: true
            };

            Plotly.newPlot('mapPlot', traces, layout);
        }

        // Create performance plot
        function createPerformancePlot() {
            const metricsData = ${JSON.stringify(metrics)};
            
            const trace = {
                x: ['Precision', 'Recall', 'F1 Score', 'Detection Rate'],
                y: [metricsData.precision, metricsData.recall, metricsData.f1Score, metricsData.detectionRate],
                type: 'bar',
                marker: { color: '${this.colors.matched}' }
            };

            const layout = {
                title: 'Performance Metrics',
                yaxis: { title: 'Score', range: [0, 1] }
            };

            Plotly.newPlot('performancePlot', [trace], layout);
        }

        // Initialize plots when page loads
        document.addEventListener('DOMContentLoaded', function() {
            createMapPlot();
            createPerformancePlot();
        });
    `;
  }
}
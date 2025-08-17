#!/usr/bin/env node

/**
 * MCP Server for PhaseNet Detection Comparison
 * 
 * This server provides tools to compare PhaseNet earthquake detections
 * with reference catalogs from JMA, USGS, and other sources.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

import { PhaseNetComparisonService } from './services/comparison.js';
import { CatalogDownloader } from './services/catalog-downloader.js';
import { EventMatcher } from './services/event-matcher.js';
import { ReportGenerator } from './services/report-generator.js';

class PhaseNetComparisonServer {
  constructor() {
    this.server = new Server(
      {
        name: 'phasenet-comparison-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.comparisonService = new PhaseNetComparisonService();
    this.catalogDownloader = new CatalogDownloader();
    this.eventMatcher = new EventMatcher();
    this.reportGenerator = new ReportGenerator();

    this.setupToolHandlers();
  }

  setupToolHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'download_reference_catalog',
            description: 'Download earthquake catalog from JMA, USGS, or other sources',
            inputSchema: {
              type: 'object',
              properties: {
                source: {
                  type: 'string',
                  enum: ['jma', 'usgs', 'ncedc', 'iris', 'scedc'],
                  description: 'Reference catalog source'
                },
                start_time: {
                  type: 'string',
                  description: 'Start time in ISO format (YYYY-MM-DDTHH:MM:SS)'
                },
                end_time: {
                  type: 'string',
                  description: 'End time in ISO format (YYYY-MM-DDTHH:MM:SS)'
                },
                min_latitude: {
                  type: 'number',
                  description: 'Minimum latitude'
                },
                max_latitude: {
                  type: 'number',
                  description: 'Maximum latitude'
                },
                min_longitude: {
                  type: 'number',
                  description: 'Minimum longitude'
                },
                max_longitude: {
                  type: 'number',
                  description: 'Maximum longitude'
                },
                min_magnitude: {
                  type: 'number',
                  description: 'Minimum magnitude',
                  default: 2.0
                },
                max_magnitude: {
                  type: 'number',
                  description: 'Maximum magnitude',
                  default: 9.0
                }
              },
              required: ['source', 'start_time', 'end_time', 'min_latitude', 'max_latitude', 'min_longitude', 'max_longitude']
            }
          },
          {
            name: 'load_phasenet_detections',
            description: 'Load PhaseNet detection results from file',
            inputSchema: {
              type: 'object',
              properties: {
                file_path: {
                  type: 'string',
                  description: 'Path to PhaseNet detection file (CSV or picks format)'
                },
                format: {
                  type: 'string',
                  enum: ['csv', 'gamma', 'picks'],
                  description: 'File format',
                  default: 'csv'
                }
              },
              required: ['file_path']
            }
          },
          {
            name: 'match_events',
            description: 'Match events between reference catalog and PhaseNet detections',
            inputSchema: {
              type: 'object',
              properties: {
                reference_events: {
                  type: 'string',
                  description: 'Reference events data (JSON string or file path)'
                },
                detected_events: {
                  type: 'string',
                  description: 'Detected events data (JSON string or file path)'
                },
                time_window: {
                  type: 'number',
                  description: 'Time window for matching (seconds)',
                  default: 30.0
                },
                distance_threshold: {
                  type: 'number',
                  description: 'Distance threshold for matching (km)',
                  default: 10.0
                },
                magnitude_diff_threshold: {
                  type: 'number',
                  description: 'Magnitude difference threshold',
                  default: 1.0
                }
              },
              required: ['reference_events', 'detected_events']
            }
          },
          {
            name: 'calculate_performance_metrics',
            description: 'Calculate detection performance metrics (precision, recall, F1)',
            inputSchema: {
              type: 'object',
              properties: {
                matching_results: {
                  type: 'string',
                  description: 'Event matching results (JSON string)'
                }
              },
              required: ['matching_results']
            }
          },
          {
            name: 'generate_comparison_report',
            description: 'Generate comprehensive comparison report with visualizations',
            inputSchema: {
              type: 'object',
              properties: {
                matching_results: {
                  type: 'string',
                  description: 'Event matching results (JSON string)'
                },
                metrics: {
                  type: 'string',
                  description: 'Performance metrics (JSON string)'
                },
                output_path: {
                  type: 'string',
                  description: 'Output file path for the report',
                  default: './comparison_report.html'
                },
                reference_source: {
                  type: 'string',
                  description: 'Reference catalog source name'
                }
              },
              required: ['matching_results', 'metrics']
            }
          },
          {
            name: 'run_full_comparison',
            description: 'Run complete comparison workflow from catalog download to report generation',
            inputSchema: {
              type: 'object',
              properties: {
                reference_source: {
                  type: 'string',
                  enum: ['jma', 'usgs', 'ncedc', 'iris', 'scedc'],
                  description: 'Reference catalog source'
                },
                phasenet_file: {
                  type: 'string',
                  description: 'Path to PhaseNet detection file'
                },
                start_time: {
                  type: 'string',
                  description: 'Start time in ISO format'
                },
                end_time: {
                  type: 'string',
                  description: 'End time in ISO format'
                },
                region: {
                  type: 'object',
                  properties: {
                    min_latitude: { type: 'number' },
                    max_latitude: { type: 'number' },
                    min_longitude: { type: 'number' },
                    max_longitude: { type: 'number' }
                  },
                  required: ['min_latitude', 'max_latitude', 'min_longitude', 'max_longitude']
                },
                output_dir: {
                  type: 'string',
                  description: 'Output directory for results',
                  default: './comparison_results'
                },
                matching_criteria: {
                  type: 'object',
                  properties: {
                    time_window: { type: 'number', default: 30.0 },
                    distance_threshold: { type: 'number', default: 10.0 },
                    magnitude_diff_threshold: { type: 'number', default: 1.0 }
                  }
                }
              },
              required: ['reference_source', 'phasenet_file', 'start_time', 'end_time', 'region']
            }
          }
        ]
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'download_reference_catalog':
            return await this.handleDownloadCatalog(args);
            
          case 'load_phasenet_detections':
            return await this.handleLoadDetections(args);
            
          case 'match_events':
            return await this.handleMatchEvents(args);
            
          case 'calculate_performance_metrics':
            return await this.handleCalculateMetrics(args);
            
          case 'generate_comparison_report':
            return await this.handleGenerateReport(args);
            
          case 'run_full_comparison':
            return await this.handleFullComparison(args);
            
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error executing tool '${name}': ${error.message}`
            }
          ],
          isError: true
        };
      }
    });
  }

  async handleDownloadCatalog(args) {
    const events = await this.catalogDownloader.downloadCatalog(args);
    
    return {
      content: [
        {
          type: 'text',
          text: `Successfully downloaded ${events.length} events from ${args.source.toUpperCase()}`
        },
        {
          type: 'text',
          text: `Events data:\n${JSON.stringify(events, null, 2)}`
        }
      ]
    };
  }

  async handleLoadDetections(args) {
    const detections = await this.comparisonService.loadPhaseNetDetections(args.file_path, args.format);
    
    return {
      content: [
        {
          type: 'text',
          text: `Successfully loaded ${detections.length} PhaseNet detections from ${args.file_path}`
        },
        {
          type: 'text',
          text: `Detections data:\n${JSON.stringify(detections, null, 2)}`
        }
      ]
    };
  }

  async handleMatchEvents(args) {
    const referenceEvents = typeof args.reference_events === 'string' && args.reference_events.startsWith('[') 
      ? JSON.parse(args.reference_events) 
      : await this.comparisonService.loadFromFile(args.reference_events);
      
    const detectedEvents = typeof args.detected_events === 'string' && args.detected_events.startsWith('[')
      ? JSON.parse(args.detected_events)
      : await this.comparisonService.loadFromFile(args.detected_events);

    const matchingResults = await this.eventMatcher.matchEvents(
      referenceEvents,
      detectedEvents,
      {
        timeWindow: args.time_window || 30.0,
        distanceThreshold: args.distance_threshold || 10.0,
        magnitudeDiffThreshold: args.magnitude_diff_threshold || 1.0
      }
    );

    return {
      content: [
        {
          type: 'text',
          text: `Event matching completed:\n- Matched pairs: ${matchingResults.matches.length}\n- Unmatched reference: ${matchingResults.unmatchedReference.length}\n- Unmatched detected: ${matchingResults.unmatchedDetected.length}`
        },
        {
          type: 'text',
          text: `Matching results:\n${JSON.stringify(matchingResults, null, 2)}`
        }
      ]
    };
  }

  async handleCalculateMetrics(args) {
    const matchingResults = JSON.parse(args.matching_results);
    const metrics = this.comparisonService.calculatePerformanceMetrics(matchingResults);

    return {
      content: [
        {
          type: 'text',
          text: `Performance metrics calculated:\n- Precision: ${metrics.precision.toFixed(3)}\n- Recall: ${metrics.recall.toFixed(3)}\n- F1 Score: ${metrics.f1Score.toFixed(3)}`
        },
        {
          type: 'text',
          text: `Full metrics:\n${JSON.stringify(metrics, null, 2)}`
        }
      ]
    };
  }

  async handleGenerateReport(args) {
    const matchingResults = JSON.parse(args.matching_results);
    const metrics = JSON.parse(args.metrics);
    
    const reportPath = await this.reportGenerator.generateReport(
      matchingResults,
      metrics,
      args.output_path || './comparison_report.html',
      args.reference_source
    );

    return {
      content: [
        {
          type: 'text',
          text: `Comparison report generated successfully at: ${reportPath}`
        }
      ]
    };
  }

  async handleFullComparison(args) {
    // Run complete workflow
    const results = await this.comparisonService.runFullComparison(args);

    return {
      content: [
        {
          type: 'text',
          text: `Complete comparison workflow finished successfully!\n\nSummary:\n- Reference events: ${results.summary.totalReferenceEvents}\n- Detected events: ${results.summary.totalDetectedEvents}\n- Matched events: ${results.summary.matchedEvents}\n- F1 Score: ${results.summary.f1Score.toFixed(3)}\n- Precision: ${results.summary.precision.toFixed(3)}\n- Recall: ${results.summary.recall.toFixed(3)}`
        },
        {
          type: 'text',
          text: `Output files:\n- Report: ${results.reportPath}\n- Matches: ${results.matchesPath}\n- Metrics: ${results.metricsPath}`
        },
        {
          type: 'text',
          text: `Full results:\n${JSON.stringify(results, null, 2)}`
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('PhaseNet Comparison MCP Server running on stdio');
  }
}

// Start the server
const server = new PhaseNetComparisonServer();
server.run().catch(console.error);
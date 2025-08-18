#!/usr/bin/env node

/**
 * Test script for PhaseNet Comparison MCP Server
 */

import { spawn } from 'child_process';
import { writeFileSync, readFileSync } from 'fs';
import path from 'path';

// Test data for demonstration
const testData = {
  reference_events: [
    {
      event_id: "jma_001",
      time: "2024-01-01T12:00:00.000Z",
      latitude: 35.6762,
      longitude: 139.6503,
      depth_km: 10.0,
      magnitude: 4.2,
      source: "JMA"
    },
    {
      event_id: "jma_002", 
      time: "2024-01-01T15:30:00.000Z",
      latitude: 35.2097,
      longitude: 139.0715,
      depth_km: 15.0,
      magnitude: 3.8,
      source: "JMA"
    }
  ],
  detected_events: [
    {
      event_id: "phasenet_001",
      time: "2024-01-01T12:00:25.000Z", // 25 seconds later
      latitude: 35.6750,
      longitude: 139.6510,
      depth_km: 12.0,
      magnitude: 4.1
    },
    {
      event_id: "phasenet_002",
      time: "2024-01-01T15:29:45.000Z", // 15 seconds earlier
      latitude: 35.2100,
      longitude: 139.0720,
      depth_km: 14.0,
      magnitude: 3.9
    },
    {
      event_id: "phasenet_003", // False positive
      time: "2024-01-01T18:00:00.000Z",
      latitude: 35.5000,
      longitude: 139.5000,
      depth_km: 8.0,
      magnitude: 3.2
    }
  ]
};

class MCPTester {
  constructor() {
    this.server = null;
    this.messageId = 1;
  }

  async startServer() {
    console.log('🚀 Starting MCP Server...');
    
    this.server = spawn('node', ['src/index.js'], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: process.cwd()
    });

    this.server.stderr.on('data', (data) => {
      console.log(`Server: ${data.toString().trim()}`);
    });

    this.server.on('error', (error) => {
      console.error('Server error:', error);
    });

    this.server.on('exit', (code) => {
      console.log(`Server exited with code: ${code}`);
    });

    // Wait a bit for server to start
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  async sendRequest(method, params = {}) {
    const request = {
      jsonrpc: "2.0",
      id: this.messageId++,
      method,
      params
    };

    console.log(`📤 Sending: ${method}`);
    console.log(`   Params: ${JSON.stringify(params, null, 2)}`);

    return new Promise((resolve, reject) => {
      let responseData = '';
      
      const onData = (data) => {
        responseData += data.toString();
        
        // Try to parse complete JSON responses
        const lines = responseData.split('\n');
        for (const line of lines) {
          if (line.trim()) {
            try {
              const response = JSON.parse(line.trim());
              if (response.id === request.id) {
                this.server.stdout.off('data', onData);
                console.log(`📥 Received response for ${method}`);
                resolve(response);
                return;
              }
            } catch (e) {
              // Not a complete JSON yet, continue
            }
          }
        }
      };

      this.server.stdout.on('data', onData);
      
      // Send the request
      this.server.stdin.write(JSON.stringify(request) + '\n');
      
      // Timeout after 30 seconds
      setTimeout(() => {
        this.server.stdout.off('data', onData);
        reject(new Error(`Timeout waiting for response to ${method}`));
      }, 30000);
    });
  }

  async testListTools() {
    console.log('\n🔍 Testing: List Tools');
    try {
      const response = await this.sendRequest('tools/list');
      if (response.result && response.result.tools) {
        console.log(`✅ Found ${response.result.tools.length} tools:`);
        response.result.tools.forEach(tool => {
          console.log(`   - ${tool.name}: ${tool.description}`);
        });
      } else {
        console.log('❌ No tools found in response');
      }
      return response.result;
    } catch (error) {
      console.error('❌ Error listing tools:', error.message);
      return null;
    }
  }

  async testEventMatching() {
    console.log('\n🔍 Testing: Event Matching');
    
    // Create temporary files for test data
    const refFile = path.join(process.cwd(), 'test_reference.json');
    const detFile = path.join(process.cwd(), 'test_detected.json');
    
    writeFileSync(refFile, JSON.stringify(testData.reference_events, null, 2));
    writeFileSync(detFile, JSON.stringify(testData.detected_events, null, 2));
    
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'match_events',
        arguments: {
          reference_events: refFile,
          detected_events: detFile,
          time_window: 30.0,
          distance_threshold: 10.0,
          magnitude_diff_threshold: 1.0
        }
      });
      
      if (response.result) {
        console.log('✅ Event matching completed');
        console.log('📊 Results:', response.result.content[0].text);
      } else {
        console.log('❌ Event matching failed:', response.error);
      }
      
      return response.result;
    } catch (error) {
      console.error('❌ Error in event matching:', error.message);
      return null;
    }
  }

  async testPerformanceMetrics() {
    console.log('\n🔍 Testing: Performance Metrics Calculation');
    
    // Mock matching results
    const mockMatchingResults = {
      matches: [
        {
          referenceIndex: 0,
          detectedIndex: 0,
          timeDiff: 25.0,
          distance: 1.2,
          magnitudeDiff: 0.1
        },
        {
          referenceIndex: 1,
          detectedIndex: 1,
          timeDiff: 15.0,
          distance: 0.8,
          magnitudeDiff: 0.1
        }
      ],
      unmatchedReference: [],
      unmatchedDetected: [testData.detected_events[2]]
    };
    
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'calculate_performance_metrics',
        arguments: {
          matching_results: JSON.stringify(mockMatchingResults)
        }
      });
      
      if (response.result) {
        console.log('✅ Performance metrics calculated');
        console.log('📊 Metrics:', response.result.content[0].text);
      } else {
        console.log('❌ Performance calculation failed:', response.error);
      }
      
      return response.result;
    } catch (error) {
      console.error('❌ Error calculating metrics:', error.message);
      return null;
    }
  }

  async testCatalogDownload() {
    console.log('\n🔍 Testing: Catalog Download (Small Test)');
    
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'download_reference_catalog',
        arguments: {
          source: 'usgs',
          start_time: '2024-01-01T00:00:00',
          end_time: '2024-01-01T01:00:00', // Small time window for testing
          min_latitude: 35.0,
          max_latitude: 36.0,
          min_longitude: 139.0,
          max_longitude: 140.0,
          min_magnitude: 3.0
        }
      });
      
      if (response.result) {
        console.log('✅ Catalog download test completed');
        console.log('📊 Results:', response.result.content[0].text);
      } else {
        console.log('❌ Catalog download failed:', response.error);
      }
      
      return response.result;
    } catch (error) {
      console.error('❌ Error downloading catalog:', error.message);
      return null;
    }
  }

  async runAllTests() {
    console.log('🧪 PhaseNet Comparison MCP Server Test Suite');
    console.log('=============================================\n');

    try {
      await this.startServer();
      
      const results = {
        listTools: await this.testListTools(),
        eventMatching: await this.testEventMatching(),
        performanceMetrics: await this.testPerformanceMetrics(),
        catalogDownload: await this.testCatalogDownload()
      };

      console.log('\n📋 Test Summary:');
      console.log('================');
      Object.entries(results).forEach(([test, result]) => {
        const status = result ? '✅' : '❌';
        console.log(`${status} ${test}`);
      });

      console.log('\n🎉 Test suite completed!');
      
    } catch (error) {
      console.error('❌ Test suite failed:', error);
    } finally {
      if (this.server) {
        this.server.kill();
      }
    }
  }

  stopServer() {
    if (this.server) {
      this.server.kill();
    }
  }
}

// Run tests if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const tester = new MCPTester();
  
  process.on('SIGINT', () => {
    console.log('\n⏹️  Stopping tests...');
    tester.stopServer();
    process.exit(0);
  });
  
  tester.runAllTests().catch(console.error);
}
/**
 * PhaseNet Detection Comparison Service
 * 
 * Core service for comparing PhaseNet earthquake detections with reference catalogs.
 */

import fs from 'fs/promises';
import csvParser from 'csv-parser';
import { createReadStream } from 'fs';
import path from 'path';

export class PhaseNetComparisonService {
  constructor() {
    this.supportedFormats = ['csv', 'gamma', 'picks'];
  }

  /**
   * Load PhaseNet detection results from file
   */
  async loadPhaseNetDetections(filePath, format = 'csv') {
    if (!this.supportedFormats.includes(format)) {
      throw new Error(`Unsupported format: ${format}. Supported formats: ${this.supportedFormats.join(', ')}`);
    }

    const exists = await fs.access(filePath).then(() => true).catch(() => false);
    if (!exists) {
      throw new Error(`File not found: ${filePath}`);
    }

    switch (format) {
      case 'csv':
        return await this.loadFromCSV(filePath);
      case 'gamma':
        return await this.loadGammaFormat(filePath);
      case 'picks':
        return await this.loadPicksFormat(filePath);
      default:
        throw new Error(`Unsupported format: ${format}`);
    }
  }

  /**
   * Load events from CSV file
   */
  async loadFromCSV(filePath) {
    try {
      const content = await fs.readFile(filePath, 'utf-8');
      const lines = content.trim().split('\n');
      
      if (lines.length < 2) {
        throw new Error('CSV file must have at least a header and one data row');
      }
      
      const headers = lines[0].split(',').map(h => h.trim());
      const events = [];
      
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        const row = {};
        
        headers.forEach((header, index) => {
          row[header] = values[index];
        });
        
        const event = this.standardizeEvent(row);
        if (event) {
          events.push(event);
        }
      }
      
      console.log(`Loaded ${events.length} events from ${filePath}`);
      return events;
      
    } catch (error) {
      throw new Error(`Error reading CSV file: ${error.message}`);
    }
  }

  /**
   * Load GaMMA format events
   */
  async loadGammaFormat(filePath) {
    // GaMMA typically outputs CSV with specific column names
    const events = await this.loadFromCSV(filePath);
    
    // Apply GaMMA-specific processing if needed
    return events.map(event => ({
      ...event,
      source: 'GAMMA'
    }));
  }

  /**
   * Load picks format (PhaseNet picks)
   */
  async loadPicksFormat(filePath) {
    // For picks format, we need to group picks into events
    const picks = await this.loadFromCSV(filePath);
    
    // Group picks by event_id or time clustering
    const events = this.groupPicksIntoEvents(picks);
    
    return events;
  }

  /**
   * Load data from file (generic)
   */
  async loadFromFile(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    
    if (ext === '.json') {
      const content = await fs.readFile(filePath, 'utf-8');
      return JSON.parse(content);
    } else if (ext === '.csv') {
      return await this.loadFromCSV(filePath);
    } else {
      throw new Error(`Unsupported file format: ${ext}`);
    }
  }

  /**
   * Standardize event data format
   */
  standardizeEvent(row) {
    // Handle various column name formats
    const columnMapping = {
      'time': ['time', 'origin_time', 'datetime', 'event_time'],
      'latitude': ['latitude', 'lat', 'event_latitude'],
      'longitude': ['longitude', 'lon', 'lng', 'event_longitude'],
      'depth_km': ['depth_km', 'depth', 'depth(km)', 'event_depth'],
      'magnitude': ['magnitude', 'mag', 'event_magnitude'],
      'event_id': ['event_id', 'id', 'idx', 'event_idx']
    };

    const event = {};
    
    // Map columns
    for (const [standardName, possibleNames] of Object.entries(columnMapping)) {
      for (const name of possibleNames) {
        if (row[name] !== undefined && row[name] !== null && row[name] !== '') {
          event[standardName] = row[name];
          break;
        }
      }
    }

    // Validate required fields
    if (!event.time || !event.latitude || !event.longitude) {
      return null; // Skip invalid events
    }

    // Convert data types
    try {
      event.latitude = parseFloat(event.latitude);
      event.longitude = parseFloat(event.longitude);
      event.depth_km = event.depth_km ? parseFloat(event.depth_km) : 10.0; // Default depth
      event.magnitude = event.magnitude ? parseFloat(event.magnitude) : null;
      
      // Ensure time is in ISO format
      if (typeof event.time === 'string' && !event.time.includes('T')) {
        // Try to parse and convert to ISO format
        const date = new Date(event.time);
        if (!isNaN(date.getTime())) {
          event.time = date.toISOString();
        }
      }
      
      return event;
    } catch (error) {
      console.warn(`Error processing event: ${error.message}`);
      return null;
    }
  }

  /**
   * Group picks into events (for picks format)
   */
  groupPicksIntoEvents(picks) {
    // This is a simplified approach - in practice, you might want more sophisticated clustering
    const events = [];
    const eventGroups = {};

    for (const pick of picks) {
      const eventId = pick.event_id || pick.id;
      
      if (!eventGroups[eventId]) {
        eventGroups[eventId] = {
          event_id: eventId,
          time: pick.time,
          latitude: pick.latitude || pick.event_latitude,
          longitude: pick.longitude || pick.event_longitude,
          depth_km: pick.depth_km || pick.event_depth || 10.0,
          magnitude: pick.magnitude || pick.event_magnitude,
          picks: []
        };
      }
      
      eventGroups[eventId].picks.push(pick);
    }

    return Object.values(eventGroups).filter(event => 
      event.latitude && event.longitude && event.time
    );
  }

  /**
   * Calculate performance metrics from matching results
   */
  calculatePerformanceMetrics(matchingResults) {
    const { matches, unmatchedReference, unmatchedDetected } = matchingResults;
    
    const truePositives = matches.length;
    const falsePositives = unmatchedDetected.length;
    const falseNegatives = unmatchedReference.length;
    
    const precision = truePositives / (truePositives + falsePositives) || 0;
    const recall = truePositives / (truePositives + falseNegatives) || 0;
    const f1Score = 2 * precision * recall / (precision + recall) || 0;
    
    // Calculate additional metrics
    const detectionRate = recall;
    const falseAlarmRate = falsePositives / (truePositives + falsePositives) || 0;
    
    // Calculate residual statistics if matches exist
    let residualStats = null;
    if (matches.length > 0) {
      const timeResiduals = matches.map(m => m.timeDiff);
      const distanceResiduals = matches.map(m => m.distance);
      const magnitudeResiduals = matches.filter(m => m.magnitudeDiff !== null).map(m => m.magnitudeDiff);
      
      residualStats = {
        time: this.calculateStats(timeResiduals),
        distance: this.calculateStats(distanceResiduals),
        magnitude: magnitudeResiduals.length > 0 ? this.calculateStats(magnitudeResiduals) : null
      };
    }

    return {
      precision,
      recall,
      f1Score,
      detectionRate,
      falseAlarmRate,
      truePositives,
      falsePositives,
      falseNegatives,
      totalReference: truePositives + falseNegatives,
      totalDetected: truePositives + falsePositives,
      residualStats
    };
  }

  /**
   * Calculate basic statistics for an array of values
   */
  calculateStats(values) {
    if (values.length === 0) return null;
    
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    const rms = Math.sqrt(values.reduce((sum, val) => sum + Math.pow(val, 2), 0) / values.length);
    
    return {
      mean,
      stdDev,
      rms,
      min: Math.min(...values),
      max: Math.max(...values),
      count: values.length
    };
  }

  /**
   * Run full comparison workflow
   */
  async runFullComparison(args) {
    const {
      reference_source,
      phasenet_file,
      start_time,
      end_time,
      region,
      output_dir = './comparison_results',
      matching_criteria = {}
    } = args;

    // Import required services
    const { CatalogDownloader } = await import('./catalog-downloader.js');
    const { EventMatcher } = await import('./event-matcher.js');
    const { ReportGenerator } = await import('./report-generator.js');
    
    const catalogDownloader = new CatalogDownloader();
    const eventMatcher = new EventMatcher();
    const reportGenerator = new ReportGenerator();

    // Create output directory
    await fs.mkdir(output_dir, { recursive: true });

    try {
      // 1. Download reference catalog
      console.log(`Downloading reference catalog from ${reference_source}...`);
      const referenceEvents = await catalogDownloader.downloadCatalog({
        source: reference_source,
        start_time,
        end_time,
        ...region
      });

      // 2. Load PhaseNet detections
      console.log(`Loading PhaseNet detections from ${phasenet_file}...`);
      const detectedEvents = await this.loadPhaseNetDetections(phasenet_file);

      // 3. Match events
      console.log('Matching events...');
      const matchingResults = await eventMatcher.matchEvents(
        referenceEvents,
        detectedEvents,
        matching_criteria
      );

      // 4. Calculate metrics
      console.log('Calculating performance metrics...');
      const metrics = this.calculatePerformanceMetrics(matchingResults);

      // 5. Save results
      const matchesPath = path.join(output_dir, 'event_matches.json');
      const metricsPath = path.join(output_dir, 'performance_metrics.json');
      const reportPath = path.join(output_dir, 'comparison_report.html');

      await fs.writeFile(matchesPath, JSON.stringify(matchingResults, null, 2));
      await fs.writeFile(metricsPath, JSON.stringify(metrics, null, 2));

      // 6. Generate report
      console.log('Generating comparison report...');
      await reportGenerator.generateReport(
        matchingResults,
        metrics,
        reportPath,
        reference_source
      );

      const summary = {
        totalReferenceEvents: referenceEvents.length,
        totalDetectedEvents: detectedEvents.length,
        matchedEvents: matchingResults.matches.length,
        f1Score: metrics.f1Score,
        precision: metrics.precision,
        recall: metrics.recall
      };

      console.log('Full comparison workflow completed successfully!');
      
      return {
        summary,
        matchingResults,
        metrics,
        matchesPath,
        metricsPath,
        reportPath
      };

    } catch (error) {
      throw new Error(`Full comparison workflow failed: ${error.message}`);
    }
  }
}
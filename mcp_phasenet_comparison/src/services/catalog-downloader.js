/**
 * Earthquake Catalog Downloader
 * 
 * Downloads earthquake catalogs from various sources (JMA, USGS, etc.)
 */

import axios from 'axios';
import { XMLParser } from 'fast-xml-parser';

export class CatalogDownloader {
  constructor() {
    this.sources = {
      usgs: {
        name: 'USGS Earthquake Catalog',
        baseUrl: 'https://earthquake.usgs.gov/fdsnws/event/1/query',
        format: 'geojson'
      },
      jma: {
        name: 'Japan Meteorological Agency (via NIED)',
        baseUrl: 'https://hinetwww11.bosai.go.jp/auth/fdsnws/event/1/query',
        format: 'xml'
      },
      ncedc: {
        name: 'Northern California Earthquake Data Center',
        baseUrl: 'https://service.ncedc.org/fdsnws/event/1/query',
        format: 'xml'
      },
      iris: {
        name: 'IRIS Data Management Center',
        baseUrl: 'https://service.iris.edu/fdsnws/event/1/query',
        format: 'xml'
      },
      scedc: {
        name: 'Southern California Earthquake Data Center',
        baseUrl: 'https://service.scedc.caltech.edu/fdsnws/event/1/query',
        format: 'xml'
      }
    };
    
    this.xmlParser = new XMLParser({
      ignoreAttributes: false,
      attributeNamePrefix: '@_'
    });
  }

  /**
   * Download earthquake catalog from specified source
   */
  async downloadCatalog({
    source,
    start_time,
    end_time,
    min_latitude,
    max_latitude,
    min_longitude,
    max_longitude,
    min_magnitude = 2.0,
    max_magnitude = 9.0
  }) {
    if (!this.sources[source]) {
      throw new Error(`Unsupported catalog source: ${source}. Available sources: ${Object.keys(this.sources).join(', ')}`);
    }

    const sourceConfig = this.sources[source];
    console.log(`Downloading catalog from ${sourceConfig.name}...`);

    try {
      const params = this.buildQueryParams({
        start_time,
        end_time,
        min_latitude,
        max_latitude,
        min_longitude,
        max_longitude,
        min_magnitude,
        max_magnitude,
        format: sourceConfig.format
      });

      const response = await axios.get(sourceConfig.baseUrl, {
        params,
        timeout: 60000, // 60 second timeout
        headers: {
          'User-Agent': 'PhaseNet-Comparison-MCP/1.0.0'
        }
      });

      let events;
      if (sourceConfig.format === 'geojson') {
        events = this.parseGeoJsonEvents(response.data);
      } else {
        events = this.parseXmlEvents(response.data);
      }

      console.log(`Successfully downloaded ${events.length} events from ${sourceConfig.name}`);
      return events;

    } catch (error) {
      if (error.response) {
        throw new Error(`HTTP ${error.response.status}: ${error.response.statusText}`);
      } else if (error.request) {
        throw new Error(`Network error: Unable to reach ${sourceConfig.name}`);
      } else {
        throw new Error(`Error downloading catalog: ${error.message}`);
      }
    }
  }

  /**
   * Build query parameters for FDSN web service
   */
  buildQueryParams({
    start_time,
    end_time,
    min_latitude,
    max_latitude,
    min_longitude,
    max_longitude,
    min_magnitude,
    max_magnitude,
    format
  }) {
    return {
      starttime: start_time,
      endtime: end_time,
      minlatitude: min_latitude,
      maxlatitude: max_latitude,
      minlongitude: min_longitude,
      maxlongitude: max_longitude,
      minmagnitude: min_magnitude,
      maxmagnitude: max_magnitude,
      format: format,
      orderby: 'time'
    };
  }

  /**
   * Parse GeoJSON events (USGS format)
   */
  parseGeoJsonEvents(data) {
    if (!data.features || !Array.isArray(data.features)) {
      throw new Error('Invalid GeoJSON format: missing features array');
    }

    return data.features.map(feature => {
      const props = feature.properties;
      const coords = feature.geometry.coordinates;

      return {
        event_id: props.ids || props.code || feature.id,
        time: new Date(props.time).toISOString(),
        latitude: coords[1],
        longitude: coords[0],
        depth_km: coords[2],
        magnitude: props.mag,
        magnitude_type: props.magType,
        location: props.place,
        source: 'USGS',
        url: props.url
      };
    }).filter(event => 
      event.latitude && event.longitude && event.time && event.magnitude
    );
  }

  /**
   * Parse XML events (QuakeML format)
   */
  parseXmlEvents(xmlData) {
    const parsed = this.xmlParser.parse(xmlData);
    
    // Handle different XML structures
    let events = [];
    
    // QuakeML format
    if (parsed.eventParameters && parsed.eventParameters.event) {
      const eventList = Array.isArray(parsed.eventParameters.event) 
        ? parsed.eventParameters.event 
        : [parsed.eventParameters.event];
      
      events = eventList.map(event => this.parseQuakeMLEvent(event));
    }
    // Alternative XML formats
    else if (parsed.events && parsed.events.event) {
      const eventList = Array.isArray(parsed.events.event) 
        ? parsed.events.event 
        : [parsed.events.event];
      
      events = eventList.map(event => this.parseSimpleXMLEvent(event));
    }
    else {
      throw new Error('Unsupported XML format: unable to find events');
    }

    return events.filter(event => 
      event && event.latitude && event.longitude && event.time
    );
  }

  /**
   * Parse QuakeML event
   */
  parseQuakeMLEvent(event) {
    try {
      // Get preferred origin or first origin
      const origins = Array.isArray(event.origin) ? event.origin : [event.origin];
      const preferredOrigin = origins.find(o => o['@_preferredOriginID'] === event['@_preferredOriginID']) || origins[0];
      
      if (!preferredOrigin) {
        return null;
      }

      // Get preferred magnitude or first magnitude
      const magnitudes = event.magnitude ? (Array.isArray(event.magnitude) ? event.magnitude : [event.magnitude]) : [];
      const preferredMagnitude = magnitudes.find(m => m['@_preferredMagnitudeID'] === event['@_preferredMagnitudeID']) || magnitudes[0];

      return {
        event_id: event['@_publicID'] || event['@_catalog:eventid'],
        time: preferredOrigin.time ? preferredOrigin.time.value : null,
        latitude: preferredOrigin.latitude ? parseFloat(preferredOrigin.latitude.value) : null,
        longitude: preferredOrigin.longitude ? parseFloat(preferredOrigin.longitude.value) : null,
        depth_km: preferredOrigin.depth ? parseFloat(preferredOrigin.depth.value) / 1000 : null, // Convert m to km
        magnitude: preferredMagnitude ? parseFloat(preferredMagnitude.mag.value) : null,
        magnitude_type: preferredMagnitude ? preferredMagnitude['@_type'] : null,
        source: this.determineSourceFromPublicID(event['@_publicID']),
        location_uncertainty_km: preferredOrigin.latitude && preferredOrigin.latitude.uncertainty 
          ? parseFloat(preferredOrigin.latitude.uncertainty) / 1000 : null
      };
    } catch (error) {
      console.warn(`Error parsing QuakeML event: ${error.message}`);
      return null;
    }
  }

  /**
   * Parse simple XML event format
   */
  parseSimpleXMLEvent(event) {
    try {
      return {
        event_id: event['@_id'] || event.id,
        time: event.time || event.origin_time,
        latitude: event.latitude ? parseFloat(event.latitude) : null,
        longitude: event.longitude ? parseFloat(event.longitude) : null,
        depth_km: event.depth ? parseFloat(event.depth) : null,
        magnitude: event.magnitude ? parseFloat(event.magnitude) : null,
        magnitude_type: event.magnitude_type,
        source: 'XML_CATALOG'
      };
    } catch (error) {
      console.warn(`Error parsing simple XML event: ${error.message}`);
      return null;
    }
  }

  /**
   * Determine source from public ID
   */
  determineSourceFromPublicID(publicID) {
    if (!publicID) return 'UNKNOWN';
    
    if (publicID.includes('usgs')) return 'USGS';
    if (publicID.includes('jma') || publicID.includes('nied')) return 'JMA';
    if (publicID.includes('ncedc')) return 'NCEDC';
    if (publicID.includes('iris')) return 'IRIS';
    if (publicID.includes('scedc')) return 'SCEDC';
    
    return 'UNKNOWN';
  }

  /**
   * Get available catalog sources
   */
  getAvailableSources() {
    return Object.keys(this.sources).map(key => ({
      id: key,
      name: this.sources[key].name,
      format: this.sources[key].format
    }));
  }

  /**
   * Test catalog source availability
   */
  async testSource(source) {
    if (!this.sources[source]) {
      throw new Error(`Unknown source: ${source}`);
    }

    const sourceConfig = this.sources[source];
    
    try {
      // Test with a minimal query
      const testParams = {
        starttime: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Yesterday
        endtime: new Date().toISOString().split('T')[0], // Today
        minlatitude: 35,
        maxlatitude: 36,
        minlongitude: 139,
        maxlongitude: 140,
        minmagnitude: 1.0,
        format: sourceConfig.format
      };

      const response = await axios.get(sourceConfig.baseUrl, {
        params: testParams,
        timeout: 10000,
        headers: {
          'User-Agent': 'PhaseNet-Comparison-MCP/1.0.0'
        }
      });

      return {
        available: true,
        status: response.status,
        source: sourceConfig.name
      };

    } catch (error) {
      return {
        available: false,
        error: error.message,
        source: sourceConfig.name
      };
    }
  }
}
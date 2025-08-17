/**
 * Event Matcher Service
 * 
 * Matches earthquake events between reference catalogs and PhaseNet detections
 * based on time, location, and magnitude criteria.
 */

import haversine from 'haversine';

export class EventMatcher {
  constructor() {
    this.defaultCriteria = {
      timeWindow: 30.0,        // seconds
      distanceThreshold: 10.0, // km
      magnitudeDiffThreshold: 1.0,
      depthDiffThreshold: 50.0 // km
    };
  }

  /**
   * Match events between reference and detected catalogs
   */
  async matchEvents(referenceEvents, detectedEvents, criteria = {}) {
    const matchingCriteria = { ...this.defaultCriteria, ...criteria };
    
    console.log(`Matching ${referenceEvents.length} reference events with ${detectedEvents.length} detected events`);
    console.log('Matching criteria:', matchingCriteria);

    // Convert time strings to Date objects for easier comparison
    const refEventsWithDates = referenceEvents.map(event => ({
      ...event,
      timeObj: new Date(event.time)
    }));

    const detEventsWithDates = detectedEvents.map(event => ({
      ...event,
      timeObj: new Date(event.time)
    }));

    const matches = [];
    const matchedRefIndices = new Set();
    const matchedDetIndices = new Set();

    // For each reference event, find the best matching detected event
    for (let refIdx = 0; refIdx < refEventsWithDates.length; refIdx++) {
      const refEvent = refEventsWithDates[refIdx];
      
      let bestMatch = null;
      let bestScore = Infinity;

      for (let detIdx = 0; detIdx < detEventsWithDates.length; detIdx++) {
        if (matchedDetIndices.has(detIdx)) {
          continue; // Already matched
        }

        const detEvent = detEventsWithDates[detIdx];
        
        // Check time window
        const timeDiff = Math.abs(refEvent.timeObj.getTime() - detEvent.timeObj.getTime()) / 1000; // seconds
        if (timeDiff > matchingCriteria.timeWindow) {
          continue;
        }

        // Check spatial distance
        const distance = this.calculateDistance(
          refEvent.latitude, refEvent.longitude,
          detEvent.latitude, detEvent.longitude
        );
        if (distance > matchingCriteria.distanceThreshold) {
          continue;
        }

        // Check magnitude difference (if both available)
        let magnitudeDiff = null;
        if (refEvent.magnitude !== null && refEvent.magnitude !== undefined &&
            detEvent.magnitude !== null && detEvent.magnitude !== undefined) {
          magnitudeDiff = Math.abs(refEvent.magnitude - detEvent.magnitude);
          if (magnitudeDiff > matchingCriteria.magnitudeDiffThreshold) {
            continue;
          }
        }

        // Check depth difference
        const refDepth = refEvent.depth_km || 10.0;
        const detDepth = detEvent.depth_km || 10.0;
        const depthDiff = Math.abs(refDepth - detDepth);
        if (depthDiff > matchingCriteria.depthDiffThreshold) {
          continue;
        }

        // Calculate combined score (lower is better)
        const score = this.calculateMatchScore(
          timeDiff, distance, magnitudeDiff, depthDiff, matchingCriteria
        );

        if (score < bestScore) {
          bestScore = score;
          bestMatch = {
            referenceIndex: refIdx,
            detectedIndex: detIdx,
            referenceEvent: refEvent,
            detectedEvent: detEvent,
            timeDiff,
            distance,
            magnitudeDiff,
            depthDiff,
            matchScore: score
          };
        }
      }

      if (bestMatch !== null) {
        matches.push(bestMatch);
        matchedRefIndices.add(refIdx);
        matchedDetIndices.add(bestMatch.detectedIndex);
      }
    }

    // Identify unmatched events
    const unmatchedReference = referenceEvents.filter((_, idx) => !matchedRefIndices.has(idx));
    const unmatchedDetected = detectedEvents.filter((_, idx) => !matchedDetIndices.has(idx));

    const results = {
      matches,
      unmatchedReference,
      unmatchedDetected,
      matchingCriteria,
      summary: {
        totalReference: referenceEvents.length,
        totalDetected: detectedEvents.length,
        matchedPairs: matches.length,
        unmatchedReference: unmatchedReference.length,
        unmatchedDetected: unmatchedDetected.length
      }
    };

    console.log(`Matching completed:`);
    console.log(`  Matched pairs: ${results.summary.matchedPairs}`);
    console.log(`  Unmatched reference: ${results.summary.unmatchedReference}`);
    console.log(`  Unmatched detected: ${results.summary.unmatchedDetected}`);

    return results;
  }

  /**
   * Calculate distance between two points using Haversine formula
   */
  calculateDistance(lat1, lon1, lat2, lon2) {
    const start = { latitude: lat1, longitude: lon1 };
    const end = { latitude: lat2, longitude: lon2 };
    
    return haversine(start, end, { unit: 'km' });
  }

  /**
   * Calculate combined match score
   */
  calculateMatchScore(timeDiff, distance, magnitudeDiff, depthDiff, criteria) {
    // Normalize each component by its threshold and apply weights
    const timeScore = (timeDiff / criteria.timeWindow) * 0.4;
    const distanceScore = (distance / criteria.distanceThreshold) * 0.4;
    const magnitudeScore = magnitudeDiff !== null 
      ? (magnitudeDiff / criteria.magnitudeDiffThreshold) * 0.15 
      : 0;
    const depthScore = (depthDiff / criteria.depthDiffThreshold) * 0.05;

    return timeScore + distanceScore + magnitudeScore + depthScore;
  }

  /**
   * Find multiple matches for a single reference event (if desired)
   */
  findMultipleMatches(referenceEvent, detectedEvents, criteria = {}, maxMatches = 3) {
    const matchingCriteria = { ...this.defaultCriteria, ...criteria };
    const refTimeObj = new Date(referenceEvent.time);
    
    const candidateMatches = [];

    for (let detIdx = 0; detIdx < detectedEvents.length; detIdx++) {
      const detEvent = detectedEvents[detIdx];
      const detTimeObj = new Date(detEvent.time);
      
      // Check basic criteria
      const timeDiff = Math.abs(refTimeObj.getTime() - detTimeObj.getTime()) / 1000;
      if (timeDiff > matchingCriteria.timeWindow) continue;

      const distance = this.calculateDistance(
        referenceEvent.latitude, referenceEvent.longitude,
        detEvent.latitude, detEvent.longitude
      );
      if (distance > matchingCriteria.distanceThreshold) continue;

      let magnitudeDiff = null;
      if (referenceEvent.magnitude !== null && detEvent.magnitude !== null) {
        magnitudeDiff = Math.abs(referenceEvent.magnitude - detEvent.magnitude);
        if (magnitudeDiff > matchingCriteria.magnitudeDiffThreshold) continue;
      }

      const refDepth = referenceEvent.depth_km || 10.0;
      const detDepth = detEvent.depth_km || 10.0;
      const depthDiff = Math.abs(refDepth - detDepth);
      if (depthDiff > matchingCriteria.depthDiffThreshold) continue;

      const score = this.calculateMatchScore(timeDiff, distance, magnitudeDiff, depthDiff, matchingCriteria);

      candidateMatches.push({
        detectedIndex: detIdx,
        detectedEvent: detEvent,
        timeDiff,
        distance,
        magnitudeDiff,
        depthDiff,
        matchScore: score
      });
    }

    // Sort by score and return top matches
    candidateMatches.sort((a, b) => a.matchScore - b.matchScore);
    return candidateMatches.slice(0, maxMatches);
  }

  /**
   * Analyze matching quality
   */
  analyzeMatchingQuality(matches) {
    if (matches.length === 0) {
      return {
        averageScore: 0,
        timeStats: null,
        distanceStats: null,
        magnitudeStats: null
      };
    }

    const scores = matches.map(m => m.matchScore);
    const timeResiduals = matches.map(m => m.timeDiff);
    const distanceResiduals = matches.map(m => m.distance);
    const magnitudeResiduals = matches
      .filter(m => m.magnitudeDiff !== null)
      .map(m => m.magnitudeDiff);

    return {
      averageScore: scores.reduce((sum, s) => sum + s, 0) / scores.length,
      scoreStats: this.calculateStats(scores),
      timeStats: this.calculateStats(timeResiduals),
      distanceStats: this.calculateStats(distanceResiduals),
      magnitudeStats: magnitudeResiduals.length > 0 ? this.calculateStats(magnitudeResiduals) : null
    };
  }

  /**
   * Calculate basic statistics
   */
  calculateStats(values) {
    if (values.length === 0) return null;

    const sorted = [...values].sort((a, b) => a - b);
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    return {
      count: values.length,
      mean,
      stdDev,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      median: sorted.length % 2 === 0 
        ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2
        : sorted[Math.floor(sorted.length / 2)],
      p25: sorted[Math.floor(sorted.length * 0.25)],
      p75: sorted[Math.floor(sorted.length * 0.75)]
    };
  }

  /**
   * Filter matches by quality threshold
   */
  filterMatchesByQuality(matches, maxScore = 1.0) {
    return matches.filter(match => match.matchScore <= maxScore);
  }

  /**
   * Generate matching summary report
   */
  generateMatchingSummary(matchingResults) {
    const { matches, summary, matchingCriteria } = matchingResults;
    const quality = this.analyzeMatchingQuality(matches);

    return {
      summary,
      matchingCriteria,
      quality,
      performance: {
        precision: summary.matchedPairs / (summary.matchedPairs + summary.unmatchedDetected),
        recall: summary.matchedPairs / (summary.matchedPairs + summary.unmatchedReference),
        matchingRate: summary.matchedPairs / summary.totalReference
      }
    };
  }
}
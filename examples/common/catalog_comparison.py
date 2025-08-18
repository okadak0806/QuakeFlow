"""
Earthquake catalog comparison and evaluation utilities.

This module provides comprehensive functionality for comparing earthquake catalogs,
calculating performance metrics, and generating evaluation reports.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

import obspy
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

from .config import RegionConfig
from .data_io import DataIO


class CatalogComparison:
    """
    Comprehensive earthquake catalog comparison and evaluation system.
    
    Supports comparison between reference catalogs (USGS, JMA, NCEDC, etc.)
    and detected events from PhaseNet/GaMMA workflows.
    """
    
    def __init__(self, config: RegionConfig, protocol: str = "file", token: Optional[str] = None, root_path: str = "./"):
        """
        Initialize catalog comparison system.
        
        Args:
            config (RegionConfig): Region configuration
            protocol (str): File protocol (file, gs, s3)
            token (str, optional): Authentication token for cloud storage
            root_path (str): Root path for file operations
        """
        self.config = config
        self.data_io = DataIO(protocol, token, root_path)
        
        # Default matching criteria - can be customized per region
        self.matching_criteria = {
            'time_window': 30.0,  # seconds
            'distance_threshold': 10.0,  # km
            'magnitude_diff_threshold': 1.0,
            'depth_diff_threshold': 50.0  # km
        }
        
        # Update with region-specific criteria if available
        if hasattr(config, 'comparison_criteria'):
            self.matching_criteria.update(config.comparison_criteria)
            
        # Initialize visualization settings
        plt.style.use('seaborn-v0_8')
        self.colors = {
            'matched': '#2E8B57',
            'unmatched_ref': '#CD5C5C', 
            'unmatched_det': '#4169E1',
            'background': '#F5F5F5'
        }
    
    def download_reference_catalog(self, 
                                 source: str = 'usgs',
                                 start_time: str = None,
                                 end_time: str = None,
                                 min_magnitude: float = 2.0,
                                 max_magnitude: float = 9.0) -> pd.DataFrame:
        """
        Download reference earthquake catalog from specified source.
        
        Args:
            source (str): Catalog source ('usgs', 'jma', 'ncedc', 'iris')
            start_time (str): Start time in ISO format
            end_time (str): End time in ISO format
            min_magnitude (float): Minimum magnitude
            max_magnitude (float): Maximum magnitude
            
        Returns:
            pd.DataFrame: Reference catalog
        """
        bounds = self.config.get_geographic_bounds()
        
        # Convert times
        if start_time is None:
            start_time = UTCDateTime.now() - 86400 * 7  # 1 week ago
        else:
            start_time = UTCDateTime(start_time)
            
        if end_time is None:
            end_time = UTCDateTime.now()
        else:
            end_time = UTCDateTime(end_time)
        
        print(f"Downloading reference catalog from {source.upper()}")
        print(f"Time range: {start_time} to {end_time}")
        print(f"Region: {bounds}")
        
        try:
            # Initialize FDSN client based on source
            source_mapping = {
                'usgs': 'USGS',
                'jma': 'NIED',  # Japan Meteorological Agency via NIED
                'ncedc': 'NCEDC',
                'iris': 'IRIS',
                'scedc': 'SCEDC'
            }
            
            client = Client(source_mapping.get(source, 'USGS'))
            
            # Download catalog
            catalog = client.get_events(
                starttime=start_time,
                endtime=end_time,
                minlatitude=bounds['minlatitude'],
                maxlatitude=bounds['maxlatitude'],
                minlongitude=bounds['minlongitude'],
                maxlongitude=bounds['maxlongitude'],
                minmagnitude=min_magnitude,
                maxmagnitude=max_magnitude
            )
            
            # Convert to DataFrame
            events_data = []
            for event in catalog:
                origin = event.preferred_origin() or event.origins[0]
                magnitude = event.preferred_magnitude() or event.magnitudes[0]
                
                events_data.append({
                    'event_id': str(event.resource_id),
                    'time': origin.time.datetime.isoformat(),
                    'latitude': origin.latitude,
                    'longitude': origin.longitude,
                    'depth_km': origin.depth / 1000.0 if origin.depth else 0.0,
                    'magnitude': magnitude.mag if magnitude else None,
                    'magnitude_type': magnitude.magnitude_type if magnitude else None,
                    'source': source.upper(),
                    'location_uncertainty_km': origin.latitude_errors.uncertainty / 1000.0 if origin.latitude_errors else None,
                    'depth_uncertainty_km': origin.depth_errors.uncertainty / 1000.0 if origin.depth_errors else None
                })
            
            reference_df = pd.DataFrame(events_data)
            print(f"Downloaded {len(reference_df)} events from {source.upper()}")
            
            return reference_df
            
        except Exception as e:
            print(f"Error downloading catalog from {source}: {e}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'event_id', 'time', 'latitude', 'longitude', 'depth_km', 
                'magnitude', 'magnitude_type', 'source'
            ])
    
    def load_detected_catalog(self, catalog_path: str) -> pd.DataFrame:
        """
        Load detected events catalog (GaMMA output).
        
        Args:
            catalog_path (str): Path to detected events catalog
            
        Returns:
            pd.DataFrame: Detected events catalog
        """
        try:
            detected_df = self.data_io.load_csv(catalog_path)
            
            # Standardize column names
            column_mapping = {
                'time': 'time',
                'latitude': 'latitude', 
                'longitude': 'longitude',
                'depth(km)': 'depth_km',
                'depth_km': 'depth_km',
                'magnitude': 'magnitude',
                'mag': 'magnitude',
                'event_id': 'event_id',
                'idx': 'event_id'
            }
            
            # Rename columns if they exist
            for old_col, new_col in column_mapping.items():
                if old_col in detected_df.columns:
                    detected_df = detected_df.rename(columns={old_col: new_col})
            
            # Ensure required columns exist
            required_columns = ['time', 'latitude', 'longitude', 'depth_km', 'magnitude']
            for col in required_columns:
                if col not in detected_df.columns:
                    if col == 'depth_km':
                        detected_df[col] = 10.0  # Default depth
                    elif col == 'magnitude':
                        detected_df[col] = np.nan
                    else:
                        raise ValueError(f"Required column '{col}' not found in detected catalog")
            
            # Add source information
            detected_df['source'] = 'DETECTED'
            
            print(f"Loaded {len(detected_df)} detected events")
            return detected_df
            
        except Exception as e:
            print(f"Error loading detected catalog: {e}")
            return pd.DataFrame()
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            float: Distance in kilometers
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth radius in kilometers
        
        return c * r
    
    def match_events(self, reference_catalog: pd.DataFrame, detected_catalog: pd.DataFrame) -> Dict[str, Any]:
        """
        Match events between reference and detected catalogs.
        
        Args:
            reference_catalog (pd.DataFrame): Reference events
            detected_catalog (pd.DataFrame): Detected events
            
        Returns:
            Dict: Matching results with detailed statistics
        """
        print("Matching events between catalogs...")
        
        # Convert time columns to datetime
        ref_times = pd.to_datetime(reference_catalog['time'])
        det_times = pd.to_datetime(detected_catalog['time'])
        
        matches = []
        matched_ref_indices = set()
        matched_det_indices = set()
        
        # For each reference event, find best matching detected event
        for ref_idx, ref_row in reference_catalog.iterrows():
            ref_time = ref_times.iloc[ref_idx]
            
            best_match = None
            best_score = float('inf')
            
            for det_idx, det_row in detected_catalog.iterrows():
                if det_idx in matched_det_indices:
                    continue
                    
                det_time = det_times.iloc[det_idx]
                
                # Time difference in seconds
                time_diff = abs((ref_time - det_time).total_seconds())
                if time_diff > self.matching_criteria['time_window']:
                    continue
                
                # Spatial distance
                distance = self.calculate_distance(
                    ref_row['latitude'], ref_row['longitude'],
                    det_row['latitude'], det_row['longitude']
                )
                if distance > self.matching_criteria['distance_threshold']:
                    continue
                
                # Magnitude difference (if both available)
                mag_diff = float('inf')
                if pd.notna(ref_row['magnitude']) and pd.notna(det_row['magnitude']):
                    mag_diff = abs(ref_row['magnitude'] - det_row['magnitude'])
                    if mag_diff > self.matching_criteria['magnitude_diff_threshold']:
                        continue
                
                # Depth difference
                depth_diff = abs(ref_row['depth_km'] - det_row['depth_km'])
                if depth_diff > self.matching_criteria['depth_diff_threshold']:
                    continue
                
                # Combined score (weighted by criteria)
                score = (time_diff / self.matching_criteria['time_window'] * 0.4 +
                        distance / self.matching_criteria['distance_threshold'] * 0.4 +
                        (mag_diff / self.matching_criteria['magnitude_diff_threshold'] if mag_diff != float('inf') else 0) * 0.2)
                
                if score < best_score:
                    best_score = score
                    best_match = {
                        'ref_idx': ref_idx,
                        'det_idx': det_idx,
                        'time_diff': time_diff,
                        'distance_km': distance,
                        'magnitude_diff': mag_diff if mag_diff != float('inf') else None,
                        'depth_diff': depth_diff,
                        'match_score': score
                    }
            
            if best_match is not None:
                matches.append(best_match)
                matched_ref_indices.add(ref_idx)
                matched_det_indices.add(best_match['det_idx'])
        
        # Create detailed matching results
        matches_df = pd.DataFrame(matches)
        
        # Unmatched events
        unmatched_reference = reference_catalog[~reference_catalog.index.isin(matched_ref_indices)]
        unmatched_detected = detected_catalog[~detected_catalog.index.isin(matched_det_indices)]
        
        results = {
            'matches': matches_df,
            'matched_reference': reference_catalog.loc[list(matched_ref_indices)] if matched_ref_indices else pd.DataFrame(),
            'matched_detected': detected_catalog.loc[list(matched_det_indices)] if matched_det_indices else pd.DataFrame(),
            'unmatched_reference': unmatched_reference,
            'unmatched_detected': unmatched_detected,
            'matching_criteria': self.matching_criteria,
            'summary': {
                'total_reference': len(reference_catalog),
                'total_detected': len(detected_catalog),
                'matched_pairs': len(matches),
                'unmatched_reference': len(unmatched_reference),
                'unmatched_detected': len(unmatched_detected)
            }
        }
        
        print(f"Matching completed:")
        print(f"  Reference events: {results['summary']['total_reference']}")
        print(f"  Detected events: {results['summary']['total_detected']}")
        print(f"  Matched pairs: {results['summary']['matched_pairs']}")
        print(f"  Unmatched reference: {results['summary']['unmatched_reference']}")
        print(f"  Unmatched detected: {results['summary']['unmatched_detected']}")
        
        return results
    
    def calculate_performance_metrics(self, matching_results: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            matching_results (Dict): Results from match_events()
            
        Returns:
            Dict: Performance metrics
        """
        summary = matching_results['summary']
        
        true_positives = summary['matched_pairs']
        false_positives = summary['unmatched_detected']
        false_negatives = summary['unmatched_reference']
        
        # Basic metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        detection_rate = true_positives / summary['total_reference'] if summary['total_reference'] > 0 else 0.0
        false_alarm_rate = false_positives / summary['total_detected'] if summary['total_detected'] > 0 else 0.0
        
        metrics = {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'detection_rate': detection_rate,
            'false_alarm_rate': false_alarm_rate,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }
        
        # Calculate magnitude-dependent metrics
        if len(matching_results['matches']) > 0:
            matched_ref = matching_results['matched_reference']
            if 'magnitude' in matched_ref.columns and not matched_ref['magnitude'].isna().all():
                mag_bins = np.arange(2.0, 7.0, 0.5)
                mag_metrics = {}
                
                for i in range(len(mag_bins) - 1):
                    mag_min, mag_max = mag_bins[i], mag_bins[i + 1]
                    mag_mask = (matched_ref['magnitude'] >= mag_min) & (matched_ref['magnitude'] < mag_max)
                    mag_count = mag_mask.sum()
                    
                    if mag_count > 0:
                        mag_metrics[f'mag_{mag_min:.1f}_{mag_max:.1f}'] = {
                            'count': int(mag_count),
                            'detection_rate': float(mag_count / len(matched_ref[mag_mask]) if len(matched_ref[mag_mask]) > 0 else 0.0)
                        }
                
                metrics['magnitude_dependent'] = mag_metrics
        
        return metrics
    
    def create_comparison_visualizations(self, 
                                       matching_results: Dict[str, Any],
                                       metrics: Dict[str, float],
                                       output_dir: str) -> List[str]:
        """
        Create comprehensive comparison visualizations.
        
        Args:
            matching_results (Dict): Matching results
            metrics (Dict): Performance metrics
            output_dir (str): Output directory for plots
            
        Returns:
            List[str]: List of generated plot files
        """
        os.makedirs(output_dir, exist_ok=True)
        generated_plots = []
        
        # 1. Event location map
        plt.figure(figsize=(12, 10))
        
        # Plot matched events
        if len(matching_results['matched_reference']) > 0:
            plt.scatter(matching_results['matched_reference']['longitude'], 
                       matching_results['matched_reference']['latitude'],
                       c=self.colors['matched'], alpha=0.7, s=50, 
                       label=f"Matched Reference ({len(matching_results['matched_reference'])})")
            
        # Plot unmatched reference events
        if len(matching_results['unmatched_reference']) > 0:
            plt.scatter(matching_results['unmatched_reference']['longitude'],
                       matching_results['unmatched_reference']['latitude'],
                       c=self.colors['unmatched_ref'], alpha=0.7, s=30,
                       label=f"Unmatched Reference ({len(matching_results['unmatched_reference'])})")
        
        # Plot unmatched detected events
        if len(matching_results['unmatched_detected']) > 0:
            plt.scatter(matching_results['unmatched_detected']['longitude'],
                       matching_results['unmatched_detected']['latitude'],
                       c=self.colors['unmatched_det'], alpha=0.7, s=30, marker='^',
                       label=f"Unmatched Detected ({len(matching_results['unmatched_detected'])})")
        
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title('Earthquake Catalog Comparison - Event Locations')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        bounds = self.config.get_geographic_bounds()
        plt.xlim(bounds['minlongitude'] - 0.1, bounds['maxlongitude'] + 0.1)
        plt.ylim(bounds['minlatitude'] - 0.1, bounds['maxlatitude'] + 0.1)
        
        location_plot = os.path.join(output_dir, 'event_locations_comparison.png')
        plt.savefig(location_plot, dpi=300, bbox_inches='tight')
        plt.close()
        generated_plots.append(location_plot)
        
        # 2. Performance metrics bar chart
        plt.figure(figsize=(10, 6))
        
        metric_names = ['Precision', 'Recall', 'F1 Score', 'Detection Rate']
        metric_values = [metrics['precision'], metrics['recall'], metrics['f1_score'], metrics['detection_rate']]
        
        bars = plt.bar(metric_names, metric_values, color=[self.colors['matched']] * len(metric_names))
        plt.ylim(0, 1)
        plt.ylabel('Score')
        plt.title('Catalog Comparison Performance Metrics')
        
        # Add value labels on bars
        for bar, value in zip(bars, metric_values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{value:.3f}', ha='center', va='bottom')
        
        plt.grid(True, alpha=0.3, axis='y')
        
        metrics_plot = os.path.join(output_dir, 'performance_metrics.png')
        plt.savefig(metrics_plot, dpi=300, bbox_inches='tight')
        plt.close()
        generated_plots.append(metrics_plot)
        
        # 3. Time and distance residuals
        if len(matching_results['matches']) > 0:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            
            matches = matching_results['matches']
            
            # Time residuals
            axes[0,0].hist(matches['time_diff'], bins=20, alpha=0.7, color=self.colors['matched'])
            axes[0,0].set_xlabel('Time Difference (seconds)')
            axes[0,0].set_ylabel('Frequency')
            axes[0,0].set_title('Time Residuals')
            axes[0,0].grid(True, alpha=0.3)
            
            # Distance residuals
            axes[0,1].hist(matches['distance_km'], bins=20, alpha=0.7, color=self.colors['matched'])
            axes[0,1].set_xlabel('Distance Difference (km)')
            axes[0,1].set_ylabel('Frequency')
            axes[0,1].set_title('Distance Residuals')
            axes[0,1].grid(True, alpha=0.3)
            
            # Magnitude residuals (if available)
            if 'magnitude_diff' in matches.columns and not matches['magnitude_diff'].isna().all():
                axes[1,0].hist(matches['magnitude_diff'].dropna(), bins=20, alpha=0.7, color=self.colors['matched'])
                axes[1,0].set_xlabel('Magnitude Difference')
                axes[1,0].set_ylabel('Frequency')
                axes[1,0].set_title('Magnitude Residuals')
                axes[1,0].grid(True, alpha=0.3)
            else:
                axes[1,0].text(0.5, 0.5, 'No magnitude data available', 
                              ha='center', va='center', transform=axes[1,0].transAxes)
                axes[1,0].set_title('Magnitude Residuals (N/A)')
            
            # Depth residuals
            axes[1,1].hist(matches['depth_diff'], bins=20, alpha=0.7, color=self.colors['matched'])
            axes[1,1].set_xlabel('Depth Difference (km)')
            axes[1,1].set_ylabel('Frequency')
            axes[1,1].set_title('Depth Residuals')
            axes[1,1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            residuals_plot = os.path.join(output_dir, 'parameter_residuals.png')
            plt.savefig(residuals_plot, dpi=300, bbox_inches='tight')
            plt.close()
            generated_plots.append(residuals_plot)
        
        # 4. Magnitude-dependent performance (if available)
        if 'magnitude_dependent' in metrics and metrics['magnitude_dependent']:
            plt.figure(figsize=(10, 6))
            
            mag_ranges = list(metrics['magnitude_dependent'].keys())
            detection_rates = [metrics['magnitude_dependent'][mag]['detection_rate'] 
                             for mag in mag_ranges]
            counts = [metrics['magnitude_dependent'][mag]['count'] 
                     for mag in mag_ranges]
            
            x_pos = np.arange(len(mag_ranges))
            bars = plt.bar(x_pos, detection_rates, color=self.colors['matched'])
            
            # Add count labels
            for bar, count in zip(bars, counts):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'n={count}', ha='center', va='bottom', fontsize=9)
            
            plt.xlabel('Magnitude Range')
            plt.ylabel('Detection Rate')
            plt.title('Magnitude-Dependent Detection Performance')
            plt.xticks(x_pos, [mag.replace('_', '-').replace('mag-', 'M') for mag in mag_ranges], rotation=45)
            plt.ylim(0, 1)
            plt.grid(True, alpha=0.3, axis='y')
            
            magnitude_plot = os.path.join(output_dir, 'magnitude_performance.png')
            plt.savefig(magnitude_plot, dpi=300, bbox_inches='tight')
            plt.close()
            generated_plots.append(magnitude_plot)
        
        print(f"Generated {len(generated_plots)} comparison plots in {output_dir}")
        return generated_plots
    
    def generate_comparison_report(self,
                                 matching_results: Dict[str, Any],
                                 metrics: Dict[str, float],
                                 reference_source: str,
                                 output_path: str) -> str:
        """
        Generate comprehensive HTML comparison report.
        
        Args:
            matching_results (Dict): Matching results
            metrics (Dict): Performance metrics  
            reference_source (str): Reference catalog source
            output_path (str): Output HTML file path
            
        Returns:
            str: Path to generated report
        """
        from datetime import datetime
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>QuakeFlow Catalog Comparison Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .metric-box {{ display: inline-block; margin: 10px; padding: 15px; 
                             background-color: #e9ecef; border-radius: 5px; text-align: center; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2E8B57; }}
                .metric-label {{ font-size: 14px; color: #666; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .summary {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌍 QuakeFlow Catalog Comparison Report</h1>
                <p><strong>Region:</strong> {self.config.region.upper()}</p>
                <p><strong>Reference Source:</strong> {reference_source.upper()}</p>
                <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <h2>📊 Performance Summary</h2>
            <div class="summary">
                <div class="metric-box">
                    <div class="metric-value">{metrics['precision']:.3f}</div>
                    <div class="metric-label">Precision</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics['recall']:.3f}</div>
                    <div class="metric-label">Recall</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics['f1_score']:.3f}</div>
                    <div class="metric-label">F1 Score</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{metrics['detection_rate']:.3f}</div>
                    <div class="metric-label">Detection Rate</div>
                </div>
            </div>
            
            <h2>📈 Event Statistics</h2>
            <table>
                <tr><th>Category</th><th>Count</th><th>Percentage</th></tr>
                <tr><td>Reference Events</td><td>{matching_results['summary']['total_reference']}</td><td>100%</td></tr>
                <tr><td>Detected Events</td><td>{matching_results['summary']['total_detected']}</td><td>-</td></tr>
                <tr><td>Matched Pairs</td><td>{matching_results['summary']['matched_pairs']}</td>
                    <td>{100*matching_results['summary']['matched_pairs']/max(matching_results['summary']['total_reference'],1):.1f}%</td></tr>
                <tr><td>Unmatched Reference</td><td>{matching_results['summary']['unmatched_reference']}</td>
                    <td>{100*matching_results['summary']['unmatched_reference']/max(matching_results['summary']['total_reference'],1):.1f}%</td></tr>
                <tr><td>Unmatched Detected</td><td>{matching_results['summary']['unmatched_detected']}</td>
                    <td>{100*matching_results['summary']['unmatched_detected']/max(matching_results['summary']['total_detected'],1):.1f}%</td></tr>
            </table>
            
            <h2>⚙️ Matching Criteria</h2>
            <table>
                <tr><th>Parameter</th><th>Threshold</th></tr>
                <tr><td>Time Window</td><td>±{self.matching_criteria['time_window']} seconds</td></tr>
                <tr><td>Distance Threshold</td><td>{self.matching_criteria['distance_threshold']} km</td></tr>
                <tr><td>Magnitude Difference</td><td>±{self.matching_criteria['magnitude_diff_threshold']}</td></tr>
                <tr><td>Depth Difference</td><td>±{self.matching_criteria['depth_diff_threshold']} km</td></tr>
            </table>
        """
        
        # Add magnitude-dependent metrics if available
        if 'magnitude_dependent' in metrics and metrics['magnitude_dependent']:
            html_content += """
            <h2>📊 Magnitude-Dependent Performance</h2>
            <table>
                <tr><th>Magnitude Range</th><th>Event Count</th><th>Detection Rate</th></tr>
            """
            for mag_range, mag_data in metrics['magnitude_dependent'].items():
                display_range = mag_range.replace('mag_', 'M').replace('_', ' - ')
                html_content += f"""
                <tr><td>{display_range}</td><td>{mag_data['count']}</td><td>{mag_data['detection_rate']:.3f}</td></tr>
                """
            html_content += "</table>"
        
        # Add residual statistics if available
        if len(matching_results['matches']) > 0:
            matches = matching_results['matches']
            html_content += f"""
            <h2>📐 Residual Statistics</h2>
            <table>
                <tr><th>Parameter</th><th>Mean</th><th>Std Dev</th><th>RMS</th></tr>
                <tr><td>Time (seconds)</td>
                    <td>{matches['time_diff'].mean():.2f}</td>
                    <td>{matches['time_diff'].std():.2f}</td>
                    <td>{np.sqrt(np.mean(matches['time_diff']**2)):.2f}</td></tr>
                <tr><td>Distance (km)</td>
                    <td>{matches['distance_km'].mean():.2f}</td>
                    <td>{matches['distance_km'].std():.2f}</td>
                    <td>{np.sqrt(np.mean(matches['distance_km']**2)):.2f}</td></tr>
                <tr><td>Depth (km)</td>
                    <td>{matches['depth_diff'].mean():.2f}</td>
                    <td>{matches['depth_diff'].std():.2f}</td>
                    <td>{np.sqrt(np.mean(matches['depth_diff']**2)):.2f}</td></tr>
            """
            
            if 'magnitude_diff' in matches.columns and not matches['magnitude_diff'].isna().all():
                mag_data = matches['magnitude_diff'].dropna()
                html_content += f"""
                <tr><td>Magnitude</td>
                    <td>{mag_data.mean():.3f}</td>
                    <td>{mag_data.std():.3f}</td>
                    <td>{np.sqrt(np.mean(mag_data**2)):.3f}</td></tr>
                """
            
            html_content += "</table>"
        
        html_content += """
            <h2>🎯 Interpretation</h2>
            <div class="summary">
        """
        
        # Add interpretation
        if metrics['f1_score'] > 0.8:
            html_content += "<p>✅ <strong>Excellent Performance:</strong> The detection system shows very high agreement with the reference catalog.</p>"
        elif metrics['f1_score'] > 0.6:
            html_content += "<p>⚠️ <strong>Good Performance:</strong> The detection system shows good agreement with room for improvement.</p>"
        else:
            html_content += "<p>❌ <strong>Poor Performance:</strong> The detection system requires significant improvement.</p>"
        
        if metrics['precision'] > 0.8:
            html_content += "<p>✅ Low false alarm rate - detected events are reliable.</p>"
        elif metrics['precision'] < 0.5:
            html_content += "<p>⚠️ High false alarm rate - many detected events are not in reference catalog.</p>"
        
        if metrics['recall'] > 0.8:
            html_content += "<p>✅ High detection rate - most reference events are being detected.</p>"
        elif metrics['recall'] < 0.5:
            html_content += "<p>⚠️ Low detection rate - many reference events are being missed.</p>"
        
        html_content += """
            </div>
            
            <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; text-align: center;">
                <p>Generated by QuakeFlow Enhanced Catalog Comparison System</p>
            </footer>
        </body>
        </html>
        """
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Comparison report generated: {output_path}")
        return output_path
    
    def run_full_comparison(self,
                          reference_catalog: pd.DataFrame,
                          detected_catalog: pd.DataFrame,
                          reference_source: str = 'unknown',
                          output_dir: str = './comparison') -> Dict[str, Any]:
        """
        Run complete catalog comparison workflow.
        
        Args:
            reference_catalog (pd.DataFrame): Reference events
            detected_catalog (pd.DataFrame): Detected events
            reference_source (str): Source of reference catalog
            output_dir (str): Output directory
            
        Returns:
            Dict: Complete comparison results
        """
        print("🌍 Running complete catalog comparison workflow...")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # 1. Match events
        matching_results = self.match_events(reference_catalog, detected_catalog)
        
        # 2. Calculate metrics
        metrics = self.calculate_performance_metrics(matching_results)
        
        # 3. Save detailed results
        # Save matches
        if len(matching_results['matches']) > 0:
            matches_path = os.path.join(output_dir, 'event_matches.csv')
            self.data_io.save_csv(matching_results['matches'], matches_path)
        
        # Save unmatched events
        unmatched_ref_path = os.path.join(output_dir, 'unmatched_reference.csv')
        self.data_io.save_csv(matching_results['unmatched_reference'], unmatched_ref_path)
        
        unmatched_det_path = os.path.join(output_dir, 'unmatched_detected.csv')
        self.data_io.save_csv(matching_results['unmatched_detected'], unmatched_det_path)
        
        # Save metrics
        metrics_path = os.path.join(output_dir, 'performance_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # 4. Create visualizations
        figures_dir = os.path.join(output_dir, 'figures')
        plot_files = self.create_comparison_visualizations(matching_results, metrics, figures_dir)
        
        # 5. Generate report
        report_path = os.path.join(output_dir, 'comparison_report.html')
        self.generate_comparison_report(matching_results, metrics, reference_source, report_path)
        
        # 6. Compile complete results
        complete_results = {
            'matching_results': matching_results,
            'metrics': metrics,
            'output_files': {
                'matches': matches_path if len(matching_results['matches']) > 0 else None,
                'unmatched_reference': unmatched_ref_path,
                'unmatched_detected': unmatched_det_path,
                'metrics': metrics_path,
                'report': report_path,
                'plots': plot_files
            },
            'summary': {
                'reference_source': reference_source,
                'region': self.config.region,
                'total_reference_events': len(reference_catalog),
                'total_detected_events': len(detected_catalog),
                'matched_events': matching_results['summary']['matched_pairs'],
                'f1_score': metrics['f1_score'],
                'precision': metrics['precision'],
                'recall': metrics['recall']
            }
        }
        
        print(f"✅ Catalog comparison completed successfully!")
        print(f"   📁 Results saved to: {output_dir}")
        print(f"   📊 F1 Score: {metrics['f1_score']:.3f}")
        print(f"   🎯 Precision: {metrics['precision']:.3f}")  
        print(f"   📈 Recall: {metrics['recall']:.3f}")
        
        return complete_results
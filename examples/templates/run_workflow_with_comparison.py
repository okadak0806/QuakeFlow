#!/usr/bin/env python3
"""
Enhanced QuakeFlow workflow with catalog comparison.

This script runs the complete earthquake analysis pipeline including catalog
comparison and validation against reference earthquake catalogs.

Features:
- Complete PhaseNet → GaMMA → ADLoc processing workflow
- Reference catalog download from multiple sources (USGS, JMA, NCEDC, etc.)
- Comprehensive event matching and performance evaluation
- Advanced visualization and reporting
- Support for multiple regions and custom configurations
"""

import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add common utilities to path
current_dir = Path(__file__).parent
examples_dir = current_dir.parent
sys.path.insert(0, str(examples_dir))

from common import (
    EarthquakeAnalysisWorkflow,
    CatalogComparison,
    RegionConfig,
    add_common_arguments,
    add_phasenet_arguments,
    add_gamma_arguments,
    add_adloc_arguments
)


def add_comparison_arguments(parser):
    """Add catalog comparison specific arguments."""
    comparison_group = parser.add_argument_group('catalog comparison options')
    
    comparison_group.add_argument(
        '--reference-source', 
        default='usgs',
        choices=['usgs', 'jma', 'ncedc', 'iris', 'scedc'],
        help='Reference catalog source (default: usgs)'
    )
    
    comparison_group.add_argument(
        '--min-magnitude',
        type=float,
        default=2.0,
        help='Minimum magnitude for reference catalog (default: 2.0)'
    )
    
    comparison_group.add_argument(
        '--max-magnitude',
        type=float,
        default=9.0,
        help='Maximum magnitude for reference catalog (default: 9.0)'
    )
    
    comparison_group.add_argument(
        '--time-window',
        type=float,
        default=30.0,
        help='Time window for event matching in seconds (default: 30.0)'
    )
    
    comparison_group.add_argument(
        '--distance-threshold',
        type=float,
        default=10.0,
        help='Distance threshold for event matching in km (default: 10.0)'
    )
    
    comparison_group.add_argument(
        '--magnitude-diff-threshold',
        type=float,
        default=1.0,
        help='Magnitude difference threshold for matching (default: 1.0)'
    )
    
    comparison_group.add_argument(
        '--skip-comparison',
        action='store_true',
        help='Skip catalog comparison step'
    )
    
    comparison_group.add_argument(
        '--comparison-only',
        action='store_true',
        help='Only run catalog comparison (skip detection pipeline)'
    )


def create_enhanced_config(args):
    """Create enhanced configuration with comparison parameters."""
    if args.config:
        config = RegionConfig.from_json(args.config)
    else:
        config = RegionConfig(args.region)
    
    # Add comparison criteria to config
    config.comparison_criteria = {
        'time_window': args.time_window,
        'distance_threshold': args.distance_threshold,
        'magnitude_diff_threshold': args.magnitude_diff_threshold
    }
    
    return config


def run_detection_workflow(args, config):
    """Run the earthquake detection workflow."""
    print("🌍 Running Enhanced Earthquake Detection Workflow...")
    
    # Initialize workflow
    workflow = EarthquakeAnalysisWorkflow(
        region=args.region,
        config_path=args.config,
        protocol=args.protocol,
        token=args.token,
        root_path=args.root_path
    )
    
    # Run complete workflow
    results = workflow.run_full_workflow(
        waveform_dir=args.waveform_dir,
        stations_file=args.stations_file,
        output_base_dir=args.output_dir,
        parallel_config={
            'num_nodes': args.num_nodes,
            'node_rank': args.node_rank
        }
    )
    
    print(f"✅ Detection workflow completed")
    print(f"   Picks: {len(results.get('picks', []))} events")
    print(f"   Events: {len(results.get('events', []))} events")
    print(f"   Relocated Events: {len(results.get('relocated_events', []))} events")
    
    return results


def run_catalog_comparison(args, config, detected_events_path=None):
    """Run catalog comparison and evaluation."""
    print("📊 Running Catalog Comparison...")
    
    # Initialize comparison system
    comparison = CatalogComparison(
        config=config,
        protocol=args.protocol,
        token=args.token,
        root_path=args.root_path
    )
    
    # Update matching criteria
    comparison.matching_criteria.update(config.comparison_criteria)
    
    # Download reference catalog
    print(f"Downloading reference catalog from {args.reference_source.upper()}...")
    reference_catalog = comparison.download_reference_catalog(
        source=args.reference_source,
        start_time=args.start_time,
        end_time=args.end_time,
        min_magnitude=args.min_magnitude,
        max_magnitude=args.max_magnitude
    )
    
    if len(reference_catalog) == 0:
        print(f"⚠️ Warning: No reference events found for comparison")
        return None
    
    # Load detected catalog
    if detected_events_path is None:
        # Try to find detected events in standard locations
        possible_paths = [
            f"{args.output_dir}/events/events_gamma.csv",
            f"{args.output_dir}/locations/events_adloc.csv",
            f"{args.output_dir}/gamma/gamma_catalog_filtered.csv",
            "gamma/gamma_catalog_filtered.csv",
            "events/events_gamma.csv"
        ]
        
        detected_events_path = None
        for path in possible_paths:
            if os.path.exists(path):
                detected_events_path = path
                break
        
        if detected_events_path is None:
            print(f"❌ Error: Could not find detected events catalog")
            print(f"   Searched paths: {possible_paths}")
            return None
    
    detected_catalog = comparison.load_detected_catalog(detected_events_path)
    
    if len(detected_catalog) == 0:
        print(f"⚠️ Warning: No detected events found for comparison")
        return None
    
    # Run comparison
    comparison_output_dir = f"{args.output_dir}/comparison"
    comparison_results = comparison.run_full_comparison(
        reference_catalog=reference_catalog,
        detected_catalog=detected_catalog,
        reference_source=args.reference_source,
        output_dir=comparison_output_dir
    )
    
    return comparison_results


def generate_integrated_report(detection_results, comparison_results, output_dir):
    """Generate integrated workflow report."""
    print("📄 Generating Integrated Workflow Report...")
    
    report_path = f"{output_dir}/integrated_workflow_report.html"
    
    # Create comprehensive HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>QuakeFlow Enhanced Workflow Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #2E8B57; }}
            .metric-box {{ display: inline-block; margin: 10px; padding: 15px; 
                         background-color: #e9ecef; border-radius: 5px; text-align: center; }}
            .metric-value {{ font-size: 20px; font-weight: bold; color: #2E8B57; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .success {{ color: #2E8B57; }}
            .warning {{ color: #FF8C00; }}
            .error {{ color: #CD5C5C; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌍 QuakeFlow Enhanced Workflow Report</h1>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h2>🔍 Detection Results</h2>
    """
    
    if detection_results:
        html_content += f"""
            <div class="metric-box">
                <div class="metric-value">{len(detection_results.get('picks', []))}</div>
                <div>Phase Picks</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{len(detection_results.get('events', []))}</div>
                <div>Associated Events</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{len(detection_results.get('relocated_events', []))}</div>
                <div>Relocated Events</div>
            </div>
        """
    else:
        html_content += "<p class='warning'>⚠️ Detection workflow was not executed</p>"
    
    html_content += "</div><div class='section'><h2>📊 Comparison Results</h2>"
    
    if comparison_results:
        summary = comparison_results['summary']
        html_content += f"""
            <div class="metric-box">
                <div class="metric-value">{summary['f1_score']:.3f}</div>
                <div>F1 Score</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{summary['precision']:.3f}</div>
                <div>Precision</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{summary['recall']:.3f}</div>
                <div>Recall</div>
            </div>
            
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Reference Events</td><td>{summary['total_reference_events']}</td></tr>
                <tr><td>Detected Events</td><td>{summary['total_detected_events']}</td></tr>
                <tr><td>Matched Events</td><td>{summary['matched_events']}</td></tr>
            </table>
        """
    else:
        html_content += "<p class='warning'>⚠️ Catalog comparison was not executed</p>"
    
    html_content += """
        </div>
        
        <div class="section">
            <h2>📁 Output Files</h2>
            <p>The following files were generated by the enhanced workflow:</p>
            <ul>
                <li><strong>Detection Results:</strong> events/, picks/, locations/</li>
                <li><strong>Comparison Results:</strong> comparison/</li>
                <li><strong>Visualizations:</strong> figures/, visualize/</li>
                <li><strong>Reports:</strong> This file and detailed comparison report</li>
            </ul>
        </div>
        
        <footer style="margin-top: 30px; text-align: center; color: #666;">
            <p>Generated by QuakeFlow Enhanced Workflow with Catalog Comparison</p>
        </footer>
    </body>
    </html>
    """
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Integrated report generated: {report_path}")
    return report_path


def main():
    """Main workflow execution function."""
    parser = argparse.ArgumentParser(
        description="Enhanced QuakeFlow workflow with catalog comparison",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete workflow with comparison
  python run_workflow_with_comparison.py \\
    --region california \\
    --waveform-dir /path/to/waveforms \\
    --stations-file /path/to/stations.json \\
    --reference-source usgs

  # Run only catalog comparison
  python run_workflow_with_comparison.py \\
    --region california \\
    --comparison-only \\
    --reference-source usgs

  # Custom matching criteria
  python run_workflow_with_comparison.py \\
    --region japan \\
    --waveform-dir /data/waveforms \\
    --stations-file /data/stations.json \\
    --reference-source jma \\
    --time-window 60 \\
    --distance-threshold 15
        """
    )
    
    # Add argument groups
    add_common_arguments(parser)
    add_phasenet_arguments(parser)
    add_gamma_arguments(parser) 
    add_adloc_arguments(parser)
    add_comparison_arguments(parser)
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.comparison_only:
        if not args.waveform_dir or not args.stations_file:
            parser.error("--waveform-dir and --stations-file are required unless --comparison-only is specified")
    
    # Create enhanced configuration
    config = create_enhanced_config(args)
    
    print(f"🚀 Starting Enhanced QuakeFlow Workflow")
    print(f"   Region: {args.region}")
    print(f"   Reference Source: {args.reference_source}")
    print(f"   Output Directory: {args.output_dir}")
    print(f"   Comparison Only: {args.comparison_only}")
    print(f"   Skip Comparison: {args.skip_comparison}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize results
    detection_results = None
    comparison_results = None
    
    try:
        # Run detection workflow (unless comparison-only)
        if not args.comparison_only:
            detection_results = run_detection_workflow(args, config)
        
        # Run catalog comparison (unless skipped)
        if not args.skip_comparison:
            comparison_results = run_catalog_comparison(args, config)
        
        # Generate integrated report
        report_path = generate_integrated_report(
            detection_results, comparison_results, args.output_dir
        )
        
        # Summary
        print(f"\n🎉 Enhanced QuakeFlow Workflow Completed Successfully!")
        print(f"   📁 Results: {args.output_dir}")
        print(f"   📄 Report: {report_path}")
        
        if comparison_results:
            summary = comparison_results['summary']
            print(f"   📊 Performance: F1={summary['f1_score']:.3f}, "
                  f"Precision={summary['precision']:.3f}, "
                  f"Recall={summary['recall']:.3f}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
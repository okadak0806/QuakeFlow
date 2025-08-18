#!/usr/bin/env python3
"""
Unified complete earthquake analysis workflow script.

This script runs the complete earthquake analysis pipeline:
1. PhaseNet phase picking
2. GaMMA event association  
3. ADLoc event relocation

Usage:
    python run_workflow.py --region california --waveform_dir /path/to/waveforms --stations_file stations.json
    python run_workflow.py --region japan --config japan_custom.json --waveform_dir /path/to/waveforms --stations_file stations.json --run_phasenet --run_gamma --run_adloc
"""

import sys
import os
import time

# Add common utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from cli import create_workflow_parser, validate_args, setup_logging
from workflow import EarthquakeAnalysisWorkflow


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = create_workflow_parser()
    args = parser.parse_args()
    
    # Validate arguments
    validate_args(args)
    
    # Setup logging
    setup_logging(args)
    
    # Initialize workflow
    workflow = EarthquakeAnalysisWorkflow(
        region=args.region,
        config_path=args.config,
        protocol=args.protocol,
        token=args.token,
        root_path=args.root_path
    )
    
    # Determine which steps to run
    run_all = not any([args.run_phasenet, args.run_gamma, args.run_adloc])
    run_phasenet = run_all or args.run_phasenet
    run_gamma = run_all or args.run_gamma
    run_adloc = run_all or args.run_adloc
    
    print(f"Starting earthquake analysis workflow for region: {args.region}")
    print(f"Steps to run: PhaseNet={run_phasenet}, GaMMA={run_gamma}, ADLoc={run_adloc}")
    
    start_time = time.time()
    
    try:
        if run_all:
            # Run complete workflow
            results = workflow.run_full_workflow(
                waveform_dir=args.waveform_dir,
                stations_file=args.stations_file,
                output_base_dir=args.output_dir
            )
        else:
            # Run partial workflow
            results = {}
            
            if run_phasenet:
                print("Running PhaseNet phase picking...")
                picks = workflow.run_phasenet_only(
                    waveform_dir=args.waveform_dir,
                    stations_file=args.stations_file,
                    output_dir=f"{args.output_dir}/picks"
                )
                results["picks"] = picks
                
            if run_gamma:
                print("Running GaMMA event association...")
                picks_file = f"{args.region}/{args.output_dir}/picks/picks_phasenet.csv"
                events, associated_picks = workflow.run_gamma_only(
                    picks_file=picks_file,
                    stations_file=args.stations_file,
                    output_dir=f"{args.output_dir}/events"
                )
                results["events"] = events
                results["associated_picks"] = associated_picks
                
            if run_adloc:
                print("Running ADLoc event relocation...")
                events_file = f"{args.region}/{args.output_dir}/events/events_gamma.csv"
                picks_file = f"{args.region}/{args.output_dir}/events/picks_gamma.csv"
                relocated_events, refined_picks = workflow.run_adloc_only(
                    events_file=events_file,
                    picks_file=picks_file,
                    stations_file=args.stations_file,
                    output_dir=f"{args.output_dir}/locations"
                )
                results["relocated_events"] = relocated_events
                results["refined_picks"] = refined_picks
        
        # Calculate processing time
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Print summary
        print("\n" + "="*60)
        print("EARTHQUAKE ANALYSIS WORKFLOW COMPLETED SUCCESSFULLY!")
        print("="*60)
        print(f"Region: {args.region}")
        print(f"Processing time: {processing_time:.1f} seconds")
        
        # Get and print summary statistics
        stats = workflow.get_summary_stats(results)
        
        if "total_picks" in stats:
            print(f"Total picks detected: {stats['total_picks']}")
            print(f"  - P-wave picks: {stats.get('p_picks', 'N/A')}")
            print(f"  - S-wave picks: {stats.get('s_picks', 'N/A')}")
            
        if "total_events" in stats:
            print(f"Events detected: {stats['total_events']}")
            if "magnitude_range" in stats:
                mag_range = stats["magnitude_range"]
                print(f"Magnitude range: {mag_range[0]:.1f} - {mag_range[1]:.1f}")
                
        if "relocated_events" in stats:
            print(f"Events relocated: {stats['relocated_events']}")
            if "mean_rms_residual" in stats:
                print(f"Mean RMS residual: {stats['mean_rms_residual']:.3f} s")
                
        print(f"Results saved to: {args.root_path}/{args.region}/{args.output_dir}/")
        print("="*60)
        
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
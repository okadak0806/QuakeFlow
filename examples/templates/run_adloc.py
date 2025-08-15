#!/usr/bin/env python3
"""
Unified ADLoc event location script for earthquake data processing.

Usage:
    python run_adloc.py --region california --events_file events.csv --picks_file picks.csv --stations_file stations.json
    python run_adloc.py --region japan --config japan_custom.json --events_file events.csv --picks_file picks.csv --stations_file stations.json
"""

import sys
import os

# Add common utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from cli import create_adloc_parser, validate_args, setup_logging
from workflow import EarthquakeAnalysisWorkflow


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = create_adloc_parser()
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
    
    # Run ADLoc relocation
    try:
        relocated_events, refined_picks = workflow.run_adloc_only(
            events_file=args.events_file,
            picks_file=args.picks_file,
            stations_file=args.stations_file,
            output_dir=args.output_dir
        )
        
        print(f"ADLoc event relocation completed successfully!")
        print(f"Region: {args.region}")
        print(f"Events relocated: {len(relocated_events)}")
        print(f"Refined picks: {len(refined_picks)}")
        print(f"Results saved to: {args.root_path}/{args.region}/{args.output_dir}/")
        
        # Print quality statistics if available
        if "rms_residual" in relocated_events.columns:
            print(f"Mean RMS residual: {relocated_events['rms_residual'].mean():.3f} s")
            print(f"Median RMS residual: {relocated_events['rms_residual'].median():.3f} s")
            
        if "location_uncertainty" in relocated_events.columns:
            print(f"Mean location uncertainty: {relocated_events['location_uncertainty'].mean():.1f} km")
            
    except Exception as e:
        print(f"Error during ADLoc relocation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
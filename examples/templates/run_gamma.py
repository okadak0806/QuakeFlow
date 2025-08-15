#!/usr/bin/env python3
"""
Unified GaMMA event association script for earthquake data processing.

Usage:
    python run_gamma.py --region california --picks_file picks.csv --stations_file stations.json
    python run_gamma.py --region japan --config japan_custom.json --picks_file picks.csv --stations_file stations.json
"""

import sys
import os

# Add common utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from cli import create_gamma_parser, validate_args, setup_logging
from workflow import EarthquakeAnalysisWorkflow


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = create_gamma_parser()
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
    
    # Run GaMMA association
    try:
        events, associated_picks = workflow.run_gamma_only(
            picks_file=args.picks_file,
            stations_file=args.stations_file,
            output_dir=args.output_dir
        )
        
        print(f"GaMMA event association completed successfully!")
        print(f"Region: {args.region}")
        print(f"Events detected: {len(events)}")
        print(f"Associated picks: {len(associated_picks)}")
        print(f"Average picks per event: {len(associated_picks) / len(events):.1f}")
        print(f"Results saved to: {args.root_path}/{args.region}/{args.output_dir}/")
        
        # Print magnitude statistics if available
        if "magnitude" in events.columns:
            print(f"Magnitude range: {events['magnitude'].min():.1f} - {events['magnitude'].max():.1f}")
            print(f"Mean magnitude: {events['magnitude'].mean():.1f}")
        
    except Exception as e:
        print(f"Error during GaMMA association: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
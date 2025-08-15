#!/usr/bin/env python3
"""
Unified PhaseNet phase picking script for earthquake data processing.

Usage:
    python run_phasenet.py --region california --waveform_dir /path/to/waveforms --stations_file stations.json
    python run_phasenet.py --region japan --config japan_custom.json --waveform_dir /path/to/waveforms --stations_file stations.json
"""

import sys
import os

# Add common utilities to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'common'))

from cli import create_phasenet_parser, validate_args, setup_logging
from workflow import EarthquakeAnalysisWorkflow


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = create_phasenet_parser()
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
    
    # Run PhaseNet processing
    try:
        picks = workflow.run_phasenet_only(
            waveform_dir=args.waveform_dir,
            stations_file=args.stations_file,
            output_dir=args.output_dir
        )
        
        print(f"PhaseNet processing completed successfully!")
        print(f"Region: {args.region}")
        print(f"Total picks detected: {len(picks)}")
        print(f"P-wave picks: {len(picks[picks['phase_type'] == 'P'])}")
        print(f"S-wave picks: {len(picks[picks['phase_type'] == 'S'])}")
        print(f"Results saved to: {args.root_path}/{args.region}/{args.output_dir}/")
        
    except Exception as e:
        print(f"Error during PhaseNet processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
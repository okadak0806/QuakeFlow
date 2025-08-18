"""
Common command line interface utilities for QuakeFlow examples.
"""

import argparse


def add_common_arguments(parser=None):
    """
    Add common command line arguments.
    
    Args:
        parser (argparse.ArgumentParser, optional): Parser to add arguments to
        
    Returns:
        argparse.ArgumentParser: Parser with common arguments
    """
    if parser is None:
        parser = argparse.ArgumentParser(description="QuakeFlow earthquake analysis")
        
    # Region and configuration
    parser.add_argument("--region", type=str, required=True,
                       help="Region name (e.g., california, japan, hawaii)")
    parser.add_argument("--config", type=str, default=None,
                       help="Path to configuration file (JSON)")
    
    # Data paths
    parser.add_argument("--root_path", type=str, default="./",
                       help="Root path for data storage")
    parser.add_argument("--protocol", type=str, default="file",
                       help="File system protocol (file, gs, s3)")
    parser.add_argument("--token", type=str, default=None,
                       help="Authentication token for cloud storage")
    
    # Processing parameters
    parser.add_argument("--num_nodes", type=int, default=1,
                       help="Number of compute nodes")
    parser.add_argument("--node_rank", type=int, default=0,
                       help="Current node rank (0-based)")
    
    # Time range
    parser.add_argument("--year", type=int, default=None,
                       help="Year to process")
    parser.add_argument("--start_time", type=str, default=None,
                       help="Start time (YYYY-MM-DDTHH:MM:SS)")
    parser.add_argument("--end_time", type=str, default=None,
                       help="End time (YYYY-MM-DDTHH:MM:SS)")
    
    # Output options
    parser.add_argument("--output_dir", type=str, default="results",
                       help="Output directory name")
    parser.add_argument("--format", type=str, default="csv",
                       choices=["csv", "json", "parquet"],
                       help="Output file format")
    
    # Processing options
    parser.add_argument("--batch_size", type=int, default=1,
                       help="Batch size for processing")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug mode")
    
    return parser


def add_phasenet_arguments(parser):
    """
    Add PhaseNet-specific arguments.
    
    Args:
        parser (argparse.ArgumentParser): Parser to add arguments to
        
    Returns:
        argparse.ArgumentParser: Parser with PhaseNet arguments
    """
    parser.add_argument("--model", type=str, default="phasenet_original",
                       help="PhaseNet model name")
    parser.add_argument("--threshold_p", type=float, default=0.3,
                       help="P phase detection threshold")
    parser.add_argument("--threshold_s", type=float, default=0.3,
                       help="S phase detection threshold")
    parser.add_argument("--input_format", type=str, default="mseed",
                       choices=["mseed", "sac", "numpy"],
                       help="Input waveform format")
    
    return parser


def add_gamma_arguments(parser):
    """
    Add GaMMA-specific arguments.
    
    Args:
        parser (argparse.ArgumentParser): Parser to add arguments to
        
    Returns:
        argparse.ArgumentParser: Parser with GaMMA arguments
    """
    parser.add_argument("--method", type=str, default="BGMM",
                       choices=["BGMM", "GMM"],
                       help="Association method")
    parser.add_argument("--oversample_factor", type=int, default=4,
                       help="Oversampling factor for association")
    parser.add_argument("--use_amplitude", action="store_true",
                       help="Use amplitude information")
    parser.add_argument("--picks_file", type=str, required=True,
                       help="Path to picks file")
    
    return parser


def add_adloc_arguments(parser):
    """
    Add ADLoc-specific arguments.
    
    Args:
        parser (argparse.ArgumentParser): Parser to add arguments to
        
    Returns:
        argparse.ArgumentParser: Parser with ADLoc arguments
    """
    parser.add_argument("--method", type=str, default="BFGS",
                       choices=["BFGS", "L-BFGS-B"],
                       help="Optimization method")
    parser.add_argument("--use_station_term", action="store_true",
                       help="Use station terms")
    parser.add_argument("--use_amplitude", action="store_true",
                       help="Use amplitude information")
    parser.add_argument("--events_file", type=str, required=True,
                       help="Path to events file")
    parser.add_argument("--picks_file", type=str, required=True,
                       help="Path to picks file")
    
    return parser


def create_phasenet_parser():
    """
    Create PhaseNet command line parser.
    
    Returns:
        argparse.ArgumentParser: Configured parser
    """
    parser = argparse.ArgumentParser(description="Run PhaseNet phase picking")
    parser = add_common_arguments(parser)
    parser = add_phasenet_arguments(parser)
    
    parser.add_argument("--waveform_dir", type=str, required=True,
                       help="Directory containing waveform files")
    parser.add_argument("--stations_file", type=str, required=True,
                       help="Path to stations file")
    
    return parser


def create_gamma_parser():
    """
    Create GaMMA command line parser.
    
    Returns:
        argparse.ArgumentParser: Configured parser
    """
    parser = argparse.ArgumentParser(description="Run GaMMA event association")
    parser = add_common_arguments(parser)
    parser = add_gamma_arguments(parser)
    
    parser.add_argument("--stations_file", type=str, required=True,
                       help="Path to stations file")
    
    return parser


def create_adloc_parser():
    """
    Create ADLoc command line parser.
    
    Returns:
        argparse.ArgumentParser: Configured parser
    """
    parser = argparse.ArgumentParser(description="Run ADLoc event location")
    parser = add_common_arguments(parser)
    parser = add_adloc_arguments(parser)
    
    parser.add_argument("--stations_file", type=str, required=True,
                       help="Path to stations file")
    
    return parser


def create_workflow_parser():
    """
    Create full workflow command line parser.
    
    Returns:
        argparse.ArgumentParser: Configured parser
    """
    parser = argparse.ArgumentParser(description="Run full earthquake analysis workflow")
    parser = add_common_arguments(parser)
    
    # Input files
    parser.add_argument("--waveform_dir", type=str, required=True,
                       help="Directory containing waveform files")
    parser.add_argument("--stations_file", type=str, required=True,
                       help="Path to stations file")
    
    # Processing steps
    parser.add_argument("--run_phasenet", action="store_true",
                       help="Run PhaseNet phase picking")
    parser.add_argument("--run_gamma", action="store_true",
                       help="Run GaMMA event association")
    parser.add_argument("--run_adloc", action="store_true",
                       help="Run ADLoc event location")
    
    # PhaseNet options
    parser.add_argument("--phasenet_model", type=str, default="phasenet_original",
                       help="PhaseNet model name")
    parser.add_argument("--threshold_p", type=float, default=0.3,
                       help="P phase detection threshold")
    parser.add_argument("--threshold_s", type=float, default=0.3,
                       help="S phase detection threshold")
    
    # GaMMA options
    parser.add_argument("--gamma_method", type=str, default="BGMM",
                       choices=["BGMM", "GMM"],
                       help="GaMMA association method")
    parser.add_argument("--oversample_factor", type=int, default=4,
                       help="Oversampling factor for association")
    
    # ADLoc options
    parser.add_argument("--adloc_method", type=str, default="BFGS",
                       choices=["BFGS", "L-BFGS-B"],
                       help="ADLoc optimization method")
    parser.add_argument("--use_station_term", action="store_true",
                       help="Use station terms in location")
    parser.add_argument("--use_amplitude", action="store_true",
                       help="Use amplitude information")
    
    return parser


def validate_args(args):
    """
    Validate command line arguments.
    
    Args:
        args (argparse.Namespace): Parsed arguments
        
    Raises:
        ValueError: If arguments are invalid
    """
    # Validate node configuration
    if args.node_rank < 0 or args.node_rank >= args.num_nodes:
        raise ValueError(f"node_rank ({args.node_rank}) must be between 0 and {args.num_nodes-1}")
    
    # Validate time arguments
    if args.start_time and args.end_time:
        from datetime import datetime
        try:
            start = datetime.fromisoformat(args.start_time)
            end = datetime.fromisoformat(args.end_time)
            if start >= end:
                raise ValueError("start_time must be before end_time")
        except ValueError as e:
            raise ValueError(f"Invalid time format: {e}")
    
    # Validate protocol
    valid_protocols = ["file", "gs", "s3", "azure"]
    if args.protocol not in valid_protocols:
        raise ValueError(f"protocol must be one of {valid_protocols}")
    
    # Validate cloud storage token
    if args.protocol != "file" and not args.token:
        print(f"Warning: Using {args.protocol} protocol without authentication token")


def setup_logging(args):
    """
    Setup logging based on command line arguments.
    
    Args:
        args (argparse.Namespace): Parsed arguments
    """
    import logging
    
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
        
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
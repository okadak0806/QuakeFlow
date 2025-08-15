"""
QuakeFlow Examples - Common Utilities

This module provides common utilities, base classes, and shared functionality
for earthquake data processing workflows across different regions.
"""

__version__ = "1.0.0"

from .base_processor import BaseProcessor
from .config import RegionConfig
from .data_io import DataIO
from .coordinates import CoordinateTransform
from .velocity_models import VelocityModel
from .processors import PhaseNetProcessor, GammaProcessor, AdlocProcessor
from .workflow import EarthquakeAnalysisWorkflow
from .elyra_utils import ElyraUtils, notebook_setup, notebook_finalize
from .cli import (
    add_common_arguments,
    add_phasenet_arguments,
    add_gamma_arguments, 
    add_adloc_arguments,
    create_phasenet_parser,
    create_gamma_parser,
    create_adloc_parser,
    create_workflow_parser,
    validate_args,
    setup_logging
)

__all__ = [
    "BaseProcessor",
    "RegionConfig", 
    "DataIO",
    "CoordinateTransform",
    "VelocityModel",
    "PhaseNetProcessor",
    "GammaProcessor", 
    "AdlocProcessor",
    "EarthquakeAnalysisWorkflow",
    "ElyraUtils",
    "notebook_setup",
    "notebook_finalize",
    "add_common_arguments",
    "add_phasenet_arguments",
    "add_gamma_arguments",
    "add_adloc_arguments", 
    "create_phasenet_parser",
    "create_gamma_parser",
    "create_adloc_parser",
    "create_workflow_parser",
    "validate_args",
    "setup_logging"
]
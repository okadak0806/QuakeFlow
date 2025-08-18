"""
Base processor class for QuakeFlow earthquake analysis workflows.
"""

import fsspec
import pandas as pd
from pyproj import Proj
from .coordinates import CoordinateTransform
from .data_io import DataIO


class BaseProcessor:
    """
    Base class for earthquake data processing workflows.
    
    Provides common functionality for data loading, coordinate transformations,
    and file system operations across different regions and protocols.
    """
    
    def __init__(self, config, region, protocol="file", token=None, root_path="./"):
        """
        Initialize the base processor.
        
        Args:
            config (dict): Configuration dictionary with region parameters
            region (str): Region name (e.g., "california", "japan")
            protocol (str): File system protocol ("file", "gs", "s3", etc.)
            token (str, optional): Authentication token for cloud storage
            root_path (str): Root path for data storage
        """
        self.config = config
        self.region = region
        self.protocol = protocol
        self.root_path = root_path
        
        # Initialize file system
        self.fs = fsspec.filesystem(protocol, token=token)
        
        # Initialize coordinate transformation
        self.coord_transform = CoordinateTransform(config)
        self.proj = self.coord_transform.proj
        
        # Initialize data I/O handler
        self.data_io = DataIO(self.fs, protocol, root_path)
        
    def load_stations(self, file_path="stations.json"):
        """
        Load station metadata and transform coordinates.
        
        Args:
            file_path (str): Path to stations file
            
        Returns:
            pd.DataFrame: Stations data with transformed coordinates
        """
        stations_path = f"{self.region}/{file_path}"
        stations = self.data_io.load_json(stations_path)
        
        # Transform coordinates
        stations = self.coord_transform.transform_stations(stations)
        
        return stations
        
    def load_events(self, file_path):
        """
        Load events data and transform coordinates.
        
        Args:
            file_path (str): Path to events file
            
        Returns:
            pd.DataFrame: Events data with transformed coordinates
        """
        events = self.data_io.load_csv(file_path)
        
        # Transform coordinates if needed
        if all(col in events.columns for col in ["longitude", "latitude"]):
            events = self.coord_transform.transform_events(events)
            
        return events
        
    def load_picks(self, file_path):
        """
        Load picks data.
        
        Args:
            file_path (str): Path to picks file
            
        Returns:
            pd.DataFrame: Picks data
        """
        return self.data_io.load_csv(file_path)
        
    def save_results(self, data, file_path, file_format="csv"):
        """
        Save results data.
        
        Args:
            data (pd.DataFrame): Data to save
            file_path (str): Output file path
            file_format (str): Output format ("csv", "json", "parquet")
        """
        self.data_io.save_data(data, file_path, file_format)
        
    def get_velocity_model(self):
        """
        Get velocity model configuration.
        
        Returns:
            dict: Velocity model parameters
        """
        if "velocity_model" in self.config:
            return self.config["velocity_model"]
        else:
            # Default simple velocity model
            return {"P": 6.0, "S": 6.0 / 1.73}
            
    def setup_processing_params(self, processor_type):
        """
        Get processing parameters for specific processor.
        
        Args:
            processor_type (str): Type of processor ("phasenet", "gamma", "adloc")
            
        Returns:
            dict: Processing parameters
        """
        if "processing" in self.config and processor_type in self.config["processing"]:
            return self.config["processing"][processor_type]
        else:
            return self._get_default_params(processor_type)
            
    def _get_default_params(self, processor_type):
        """Get default processing parameters."""
        defaults = {
            "phasenet": {
                "batch_size": 1,
                "model": "phasenet_original"
            },
            "gamma": {
                "vel": {"P": 6.0, "S": 6.0 / 1.73},
                "dims": ["x_km", "y_km", "z_km"],
                "use_amplitude": True
            },
            "adloc": {
                "vel": {"P": 6.0, "S": 6.0 / 1.73},
                "use_amplitude": True,
                "method": "BFGS"
            }
        }
        return defaults.get(processor_type, {})
        
    def validate_data(self, data, required_columns):
        """
        Validate that data contains required columns.
        
        Args:
            data (pd.DataFrame): Data to validate
            required_columns (list): List of required column names
            
        Raises:
            ValueError: If required columns are missing
        """
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
            
    def log_info(self, message):
        """Log information message."""
        print(f"[{self.region.upper()}] {message}")
        
    def log_warning(self, message):
        """Log warning message."""
        print(f"[{self.region.upper()}] WARNING: {message}")
        
    def log_error(self, message):
        """Log error message."""
        print(f"[{self.region.upper()}] ERROR: {message}")
"""
Configuration management for QuakeFlow examples.
"""

import json
import os
from pathlib import Path
from .velocity_models import VelocityModel


class RegionConfig:
    """
    Regional configuration management for earthquake data processing.
    """
    
    def __init__(self, region_name, config_dict=None):
        """
        Initialize region configuration.
        
        Args:
            region_name (str): Name of the region
            config_dict (dict, optional): Configuration dictionary
        """
        self.region = region_name
        
        if config_dict is not None:
            self.config = config_dict
        else:
            self.config = self._load_default_config()
            
        self._validate_config()
        
    def _load_default_config(self):
        """Load default configuration for the region."""
        return self._get_region_defaults(self.region)
        
    def _get_region_defaults(self, region):
        """Get default configuration for specific regions."""
        defaults = {
            "california": {
                "region": "california",
                "geographic_bounds": {
                    "minlatitude": 32.0,
                    "maxlatitude": 43.0,
                    "minlongitude": -126.0,
                    "maxlongitude": -114.0
                },
                "velocity_model": {
                    "type": "layered_1d",
                    "layers": {
                        "depths": [0.0, 5.5, 16.0, 32.0],
                        "vp": [5.5, 5.5, 6.7, 7.8],
                        "vs": [3.18, 3.18, 3.87, 4.51]
                    }
                },
                "processing": {
                    "phasenet": {
                        "batch_size": 1,
                        "model": "phasenet_original",
                        "threshold_p": 0.3,
                        "threshold_s": 0.3
                    },
                    "gamma": {
                        "vel": {"P": 6.0, "S": 6.0 / 1.73},
                        "dims": ["x_km", "y_km", "z_km"],
                        "use_amplitude": True,
                        "method": "BGMM",
                        "oversample_factor": 4
                    },
                    "adloc": {
                        "vel": {"P": 6.0, "S": 6.0 / 1.73},
                        "use_amplitude": True,
                        "method": "BFGS",
                        "use_station_term": True
                    }
                }
            },
            "japan": {
                "region": "japan",
                "geographic_bounds": {
                    "minlatitude": 30.0,
                    "maxlatitude": 46.0,
                    "minlongitude": 129.0,
                    "maxlongitude": 146.0
                },
                "velocity_model": {
                    "type": "layered_1d",
                    "layers": {
                        "depths": [0.0, 3.0, 16.0, 32.0],
                        "vp": [5.5, 6.0, 6.7, 7.8],
                        "vs": [3.18, 3.47, 3.87, 4.51]
                    }
                },
                "processing": {
                    "phasenet": {
                        "batch_size": 1,
                        "model": "phasenet_original",
                        "threshold_p": 0.3,
                        "threshold_s": 0.3
                    },
                    "gamma": {
                        "vel": {"P": 6.0, "S": 6.0 / 1.73},
                        "dims": ["x_km", "y_km", "z_km"],
                        "use_amplitude": True,
                        "method": "BGMM",
                        "oversample_factor": 4
                    },
                    "adloc": {
                        "vel": {"P": 6.0, "S": 6.0 / 1.73},
                        "use_amplitude": True,
                        "method": "BFGS",
                        "use_station_term": True
                    }
                }
            },
            "hawaii": {
                "region": "hawaii",
                "geographic_bounds": {
                    "minlatitude": 18.0,
                    "maxlatitude": 23.0,
                    "minlongitude": -161.0,
                    "maxlongitude": -154.0
                },
                "velocity_model": {
                    "type": "simple",
                    "vp": 5.8,
                    "vs": 3.35
                },
                "processing": {
                    "phasenet": {
                        "batch_size": 1,
                        "model": "phasenet_original",
                        "threshold_p": 0.3,
                        "threshold_s": 0.3
                    },
                    "gamma": {
                        "vel": {"P": 5.8, "S": 3.35},
                        "dims": ["x_km", "y_km", "z_km"],
                        "use_amplitude": True,
                        "method": "BGMM",
                        "oversample_factor": 4
                    },
                    "adloc": {
                        "vel": {"P": 5.8, "S": 3.35},
                        "use_amplitude": True,
                        "method": "BFGS",
                        "use_station_term": True
                    }
                }
            }
        }
        
        if region.lower() in defaults:
            return defaults[region.lower()]
        else:
            # Return generic default
            return defaults["california"]
            
    def _validate_config(self):
        """Validate configuration completeness."""
        required_keys = ["region", "geographic_bounds", "velocity_model", "processing"]
        
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"Missing required configuration key: {key}")
                
        # Validate geographic bounds
        bounds = self.config["geographic_bounds"]
        required_bounds = ["minlatitude", "maxlatitude", "minlongitude", "maxlongitude"]
        
        for bound in required_bounds:
            if bound not in bounds:
                raise ValueError(f"Missing geographic bound: {bound}")
                
        # Copy bounds to top level for backward compatibility
        for bound in required_bounds:
            self.config[bound] = bounds[bound]
            
    @classmethod
    def from_json(cls, config_path):
        """
        Load configuration from JSON file.
        
        Args:
            config_path (str): Path to configuration file
            
        Returns:
            RegionConfig: Loaded configuration
        """
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
            
        region_name = config_dict.get("region", "unknown")
        return cls(region_name, config_dict)
        
    @classmethod
    def from_dict(cls, config_dict):
        """
        Create configuration from dictionary.
        
        Args:
            config_dict (dict): Configuration dictionary
            
        Returns:
            RegionConfig: Configuration object
        """
        region_name = config_dict.get("region", "unknown")
        return cls(region_name, config_dict)
        
    def save_json(self, output_path):
        """
        Save configuration to JSON file.
        
        Args:
            output_path (str): Output file path
        """
        with open(output_path, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def get_velocity_model(self):
        """
        Get velocity model object.
        
        Returns:
            VelocityModel: Configured velocity model
        """
        return VelocityModel.from_config(self.config)
        
    def get_processing_config(self, processor_type):
        """
        Get processing configuration for specific processor.
        
        Args:
            processor_type (str): Processor type ("phasenet", "gamma", "adloc")
            
        Returns:
            dict: Processing configuration
        """
        return self.config["processing"].get(processor_type, {})
        
    def get_geographic_bounds(self):
        """
        Get geographic bounds.
        
        Returns:
            dict: Geographic bounds
        """
        return self.config["geographic_bounds"]
        
    def update_bounds(self, minlat, maxlat, minlon, maxlon):
        """
        Update geographic bounds.
        
        Args:
            minlat (float): Minimum latitude
            maxlat (float): Maximum latitude
            minlon (float): Minimum longitude
            maxlon (float): Maximum longitude
        """
        bounds = {
            "minlatitude": minlat,
            "maxlatitude": maxlat,
            "minlongitude": minlon,
            "maxlongitude": maxlon
        }
        
        self.config["geographic_bounds"] = bounds
        
        # Update top-level keys for backward compatibility
        for key, value in bounds.items():
            self.config[key] = value
            
    def update_processing_param(self, processor_type, param_name, param_value):
        """
        Update processing parameter.
        
        Args:
            processor_type (str): Processor type
            param_name (str): Parameter name
            param_value: Parameter value
        """
        if processor_type not in self.config["processing"]:
            self.config["processing"][processor_type] = {}
            
        self.config["processing"][processor_type][param_name] = param_value
        
    def get_config_dict(self):
        """
        Get configuration as dictionary.
        
        Returns:
            dict: Configuration dictionary
        """
        return self.config.copy()
        
    def merge_config(self, other_config):
        """
        Merge another configuration into this one.
        
        Args:
            other_config (dict or RegionConfig): Configuration to merge
        """
        if isinstance(other_config, RegionConfig):
            other_dict = other_config.get_config_dict()
        else:
            other_dict = other_config
            
        def deep_merge(dict1, dict2):
            """Deep merge two dictionaries."""
            result = dict1.copy()
            for key, value in dict2.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
            
        self.config = deep_merge(self.config, other_dict)
        self._validate_config()
        
    def __getitem__(self, key):
        """Allow dictionary-style access."""
        return self.config[key]
        
    def __setitem__(self, key, value):
        """Allow dictionary-style assignment."""
        self.config[key] = value
        
    def __contains__(self, key):
        """Allow 'in' operator."""
        return key in self.config
        
    def get(self, key, default=None):
        """Get with default value."""
        return self.config.get(key, default)
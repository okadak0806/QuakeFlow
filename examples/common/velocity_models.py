"""
Velocity model utilities for QuakeFlow examples.
"""

import numpy as np


class VelocityModel:
    """
    Velocity model handler for earthquake location.
    """
    
    def __init__(self, model_type="simple", **kwargs):
        """
        Initialize velocity model.
        
        Args:
            model_type (str): Type of velocity model ("simple", "layered_1d", "3d")
            **kwargs: Model-specific parameters
        """
        self.model_type = model_type
        self.kwargs = kwargs
        self._setup_model()
        
    def _setup_model(self):
        """Setup velocity model based on type."""
        if self.model_type == "simple":
            self._setup_simple_model()
        elif self.model_type == "layered_1d":
            self._setup_layered_1d_model()
        elif self.model_type == "3d":
            self._setup_3d_model()
        else:
            raise ValueError(f"Unknown velocity model type: {self.model_type}")
            
    def _setup_simple_model(self):
        """Setup simple constant velocity model."""
        self.vp = self.kwargs.get("vp", 6.0)
        self.vs = self.kwargs.get("vs", self.vp / 1.73)
        self.vp_vs_ratio = self.vp / self.vs
        
        self.vel = {"P": self.vp, "S": self.vs}
        
    def _setup_layered_1d_model(self):
        """Setup 1D layered velocity model."""
        # Default NCEDC-like model
        if "layers" in self.kwargs:
            layers = self.kwargs["layers"]
            self.depths = layers["depths"]
            self.vp_values = layers["vp"]
            self.vs_values = layers["vs"]
        else:
            # Default layered model
            self.depths = [0.0, 5.5, 16.0, 32.0]
            self.vp_values = [5.5, 5.5, 6.7, 7.8]
            self.vp_vs_ratio = self.kwargs.get("vp_vs_ratio", 1.73)
            self.vs_values = [vp / self.vp_vs_ratio for vp in self.vp_values]
            
        # Create velocity structure for GaMMA/ADLoc
        self.vel = {
            "z": self.depths,
            "p": self.vp_values,
            "s": self.vs_values
        }
        
    def _setup_3d_model(self):
        """Setup 3D velocity model (placeholder)."""
        # This would require more complex implementation
        # For now, fall back to simple model
        self._setup_simple_model()
        
    def get_gamma_config(self):
        """
        Get velocity configuration for GaMMA.
        
        Returns:
            dict: Velocity configuration for GaMMA
        """
        if self.model_type == "simple":
            return {"P": self.vp, "S": self.vs}
        elif self.model_type == "layered_1d":
            return self.vel
        else:
            return {"P": self.vp, "S": self.vs}
            
    def get_adloc_config(self):
        """
        Get velocity configuration for ADLoc.
        
        Returns:
            dict: Velocity configuration for ADLoc
        """
        return self.get_gamma_config()
        
    def get_travel_time(self, distance, depth, phase="P"):
        """
        Calculate travel time for given distance and depth.
        
        Args:
            distance (float): Epicentral distance in km
            depth (float): Source depth in km
            phase (str): Seismic phase ("P" or "S")
            
        Returns:
            float: Travel time in seconds
        """
        if self.model_type == "simple":
            velocity = self.vp if phase == "P" else self.vs
            hypocentral_distance = np.sqrt(distance**2 + depth**2)
            return hypocentral_distance / velocity
        elif self.model_type == "layered_1d":
            # Simplified calculation - would need ray tracing for accuracy
            avg_velocity = np.mean(self.vp_values if phase == "P" else self.vs_values)
            hypocentral_distance = np.sqrt(distance**2 + depth**2)
            return hypocentral_distance / avg_velocity
        else:
            return self.get_travel_time(distance, depth, phase)
            
    def get_station_terms(self, stations):
        """
        Calculate station terms (placeholder).
        
        Args:
            stations (pd.DataFrame): Station data
            
        Returns:
            dict: Station terms for P and S phases
        """
        # This is a placeholder - station terms would typically be calculated
        # from observed residuals or 3D velocity models
        station_terms = {}
        for _, station in stations.iterrows():
            station_id = station.get("id", station.get("station"))
            station_terms[station_id] = {"P": 0.0, "S": 0.0}
            
        return station_terms
        
    @classmethod
    def from_config(cls, config):
        """
        Create velocity model from configuration.
        
        Args:
            config (dict): Configuration dictionary
            
        Returns:
            VelocityModel: Configured velocity model
        """
        if "velocity_model" in config:
            vm_config = config["velocity_model"]
            model_type = vm_config.get("type", "simple")
            return cls(model_type=model_type, **vm_config)
        else:
            # Default simple model
            return cls(model_type="simple")
            
    @classmethod
    def get_california_model(cls):
        """Get standard California velocity model."""
        return cls(
            model_type="layered_1d",
            layers={
                "depths": [0.0, 5.5, 16.0, 32.0],
                "vp": [5.5, 5.5, 6.7, 7.8],
                "vs": [3.18, 3.18, 3.87, 4.51]
            }
        )
        
    @classmethod
    def get_japan_model(cls):
        """Get standard Japan velocity model."""
        return cls(
            model_type="layered_1d", 
            layers={
                "depths": [0.0, 3.0, 16.0, 32.0],
                "vp": [5.5, 6.0, 6.7, 7.8],
                "vs": [3.18, 3.47, 3.87, 4.51]
            }
        )
        
    @classmethod
    def get_simple_model(cls, vp=6.0, vp_vs_ratio=1.73):
        """Get simple constant velocity model."""
        return cls(
            model_type="simple",
            vp=vp,
            vs=vp/vp_vs_ratio
        )
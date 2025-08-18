"""
Coordinate transformation utilities for QuakeFlow examples.
"""

import pandas as pd
from pyproj import Proj


class CoordinateTransform:
    """
    Coordinate transformation handler for earthquake data.
    """
    
    def __init__(self, config):
        """
        Initialize coordinate transformer.
        
        Args:
            config (dict): Configuration with geographic bounds
        """
        self.config = config
        self.proj = self._setup_projection()
        
    def _setup_projection(self):
        """
        Setup map projection for coordinate transformation.
        
        Returns:
            pyproj.Proj: Projection object
        """
        # Calculate center coordinates
        lon0 = (self.config["minlongitude"] + self.config["maxlongitude"]) / 2
        lat0 = (self.config["minlatitude"] + self.config["maxlatitude"]) / 2
        
        # Setup stereographic projection
        proj_string = f"+proj=sterea +lon_0={lon0} +lat_0={lat0} +units=km"
        return Proj(proj_string)
        
    def transform_coordinates(self, longitude, latitude):
        """
        Transform longitude/latitude to projected coordinates.
        
        Args:
            longitude (float or array): Longitude values
            latitude (float or array): Latitude values
            
        Returns:
            tuple: (x_km, y_km) projected coordinates
        """
        return self.proj(longitude=longitude, latitude=latitude)
        
    def inverse_transform(self, x_km, y_km):
        """
        Transform projected coordinates back to longitude/latitude.
        
        Args:
            x_km (float or array): X coordinates in km
            y_km (float or array): Y coordinates in km
            
        Returns:
            tuple: (longitude, latitude) geographic coordinates
        """
        return self.proj(x_km, y_km, inverse=True)
        
    def transform_stations(self, stations):
        """
        Transform station coordinates and add elevation.
        
        Args:
            stations (pd.DataFrame): Stations data with longitude, latitude columns
            
        Returns:
            pd.DataFrame: Stations with added x_km, y_km, z_km columns
        """
        if isinstance(stations, dict):
            stations = pd.DataFrame(stations)
            
        # Transform coordinates
        stations[["x_km", "y_km"]] = stations.apply(
            lambda row: pd.Series(self.transform_coordinates(row.longitude, row.latitude)), 
            axis=1
        )
        
        # Add depth coordinate (negative elevation)
        if "elevation_m" in stations.columns:
            stations["z_km"] = stations["elevation_m"].apply(lambda x: -x / 1000.0)
        elif "elevation" in stations.columns:
            stations["z_km"] = stations["elevation"].apply(lambda x: -x / 1000.0)
        else:
            # Default elevation if not available
            stations["z_km"] = 0.0
            
        return stations
        
    def transform_events(self, events):
        """
        Transform event coordinates.
        
        Args:
            events (pd.DataFrame): Events data with longitude, latitude columns
            
        Returns:
            pd.DataFrame: Events with added x_km, y_km columns
        """
        # Transform coordinates
        events[["x_km", "y_km"]] = events.apply(
            lambda row: pd.Series(self.transform_coordinates(row.longitude, row.latitude)),
            axis=1
        )
        
        # Handle depth column
        if "depth_km" not in events.columns:
            if "depth" in events.columns:
                events["depth_km"] = events["depth"]
            else:
                events["depth_km"] = 5.0  # Default depth
                
        # Ensure z_km column for consistency
        events["z_km"] = events["depth_km"]
        
        return events
        
    def add_distance_columns(self, picks, stations, events):
        """
        Add epicentral and hypocentral distances to picks.
        
        Args:
            picks (pd.DataFrame): Picks data
            stations (pd.DataFrame): Stations data with x_km, y_km, z_km
            events (pd.DataFrame): Events data with x_km, y_km, z_km
            
        Returns:
            pd.DataFrame: Picks with added distance columns
        """
        # Merge station coordinates
        picks = picks.merge(
            stations[["id", "x_km", "y_km", "z_km"]].rename(columns={
                "id": "station_id", 
                "x_km": "station_x_km", 
                "y_km": "station_y_km", 
                "z_km": "station_z_km"
            }),
            on="station_id",
            how="left"
        )
        
        # Merge event coordinates
        picks = picks.merge(
            events[["event_id", "x_km", "y_km", "z_km"]].rename(columns={
                "x_km": "event_x_km",
                "y_km": "event_y_km", 
                "z_km": "event_z_km"
            }),
            on="event_id",
            how="left"
        )
        
        # Calculate epicentral distance
        picks["epicentral_distance_km"] = (
            (picks["station_x_km"] - picks["event_x_km"])**2 +
            (picks["station_y_km"] - picks["event_y_km"])**2
        )**0.5
        
        # Calculate hypocentral distance
        picks["hypocentral_distance_km"] = (
            (picks["station_x_km"] - picks["event_x_km"])**2 +
            (picks["station_y_km"] - picks["event_y_km"])**2 +
            (picks["station_z_km"] - picks["event_z_km"])**2
        )**0.5
        
        return picks
        
    def get_region_bounds_km(self):
        """
        Get region bounds in projected coordinates.
        
        Returns:
            dict: Region bounds in km coordinates
        """
        # Transform corner coordinates
        x_min, y_min = self.transform_coordinates(
            self.config["minlongitude"], 
            self.config["minlatitude"]
        )
        x_max, y_max = self.transform_coordinates(
            self.config["maxlongitude"], 
            self.config["maxlatitude"]
        )
        
        return {
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max
        }
        
    def is_within_bounds(self, longitude, latitude):
        """
        Check if coordinates are within region bounds.
        
        Args:
            longitude (float or array): Longitude values
            latitude (float or array): Latitude values
            
        Returns:
            bool or array: True if within bounds
        """
        lon_check = (longitude >= self.config["minlongitude"]) & (longitude <= self.config["maxlongitude"])
        lat_check = (latitude >= self.config["minlatitude"]) & (latitude <= self.config["maxlatitude"])
        
        return lon_check & lat_check
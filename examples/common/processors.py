"""
Earthquake data processing workflow components.
"""

import pandas as pd
from .base_processor import BaseProcessor


class PhaseNetProcessor(BaseProcessor):
    """
    PhaseNet phase picking processor.
    """
    
    def __init__(self, config, region, protocol="file", token=None, root_path="./"):
        super().__init__(config, region, protocol, token, root_path)
        self.phasenet_config = self.setup_processing_params("phasenet")
        
    def process_waveforms(self, waveform_dir, stations_file, output_dir="picks"):
        """
        Process waveforms using PhaseNet.
        
        Args:
            waveform_dir (str): Directory containing waveforms
            stations_file (str): Path to stations file
            output_dir (str): Output directory for picks
            
        Returns:
            pd.DataFrame: Detected picks
        """
        self.log_info("Starting PhaseNet phase picking")
        
        # Load stations
        stations = self.load_stations(stations_file)
        
        # Setup PhaseNet parameters
        threshold_p = self.phasenet_config.get("threshold_p", 0.3)
        threshold_s = self.phasenet_config.get("threshold_s", 0.3)
        batch_size = self.phasenet_config.get("batch_size", 1)
        
        self.log_info(f"Using thresholds: P={threshold_p}, S={threshold_s}")
        
        # This is a placeholder for the actual PhaseNet processing
        # In a real implementation, this would call the PhaseNet model
        picks = self._run_phasenet(waveform_dir, stations, threshold_p, threshold_s, batch_size)
        
        # Save picks
        output_path = f"{self.region}/{output_dir}/picks_phasenet.csv"
        self.save_results(picks, output_path)
        
        self.log_info(f"Completed PhaseNet processing. Found {len(picks)} picks")
        return picks
        
    def _run_phasenet(self, waveform_dir, stations, threshold_p, threshold_s, batch_size):
        """
        Run PhaseNet model (placeholder implementation).
        
        This would be replaced with actual PhaseNet model calls.
        """
        # Placeholder implementation
        import numpy as np
        from datetime import datetime, timedelta
        
        picks = []
        base_time = datetime.now()
        
        for i, (_, station) in enumerate(stations.iterrows()):
            # Simulate some picks for each station
            n_picks = np.random.poisson(5)  # Average 5 picks per station
            
            for j in range(n_picks):
                pick_time = base_time + timedelta(minutes=np.random.randint(0, 1440))
                phase = np.random.choice(["P", "S"])
                probability = np.random.uniform(0.3, 0.95)
                
                picks.append({
                    "station_id": station.get("id", station.get("station")),
                    "phase_time": pick_time.isoformat(),
                    "phase_type": phase,
                    "phase_probability": probability,
                    "phase_amplitude": np.random.lognormal(0, 1)
                })
                
        return pd.DataFrame(picks)


class GammaProcessor(BaseProcessor):
    """
    GaMMA event association processor.
    """
    
    def __init__(self, config, region, protocol="file", token=None, root_path="./"):
        super().__init__(config, region, protocol, token, root_path)
        self.gamma_config = self.setup_processing_params("gamma")
        
    def associate_events(self, picks_file, stations_file, output_dir="events"):
        """
        Associate picks into events using GaMMA.
        
        Args:
            picks_file (str): Path to picks file
            stations_file (str): Path to stations file
            output_dir (str): Output directory for events
            
        Returns:
            tuple: (events DataFrame, associated picks DataFrame)
        """
        self.log_info("Starting GaMMA event association")
        
        # Load data
        picks = self.load_picks(picks_file)
        stations = self.load_stations(stations_file)
        
        # Validate required columns
        self.validate_data(picks, ["station_id", "phase_time", "phase_type"])
        self.validate_data(stations, ["id", "longitude", "latitude"])
        
        # Setup GaMMA parameters
        velocity_model = self.get_velocity_model()
        method = self.gamma_config.get("method", "BGMM")
        use_amplitude = self.gamma_config.get("use_amplitude", True)
        
        self.log_info(f"Using method: {method}, velocity model: {velocity_model}")
        
        # Add coordinate information to picks
        picks = self._add_station_coordinates(picks, stations)
        
        # Run GaMMA association
        events, associated_picks = self._run_gamma(picks, stations, velocity_model, method, use_amplitude)
        
        # Save results
        events_path = f"{self.region}/{output_dir}/events_gamma.csv"
        picks_path = f"{self.region}/{output_dir}/picks_gamma.csv"
        
        self.save_results(events, events_path)
        self.save_results(associated_picks, picks_path)
        
        self.log_info(f"Completed GaMMA association. Found {len(events)} events with {len(associated_picks)} picks")
        return events, associated_picks
        
    def _add_station_coordinates(self, picks, stations):
        """Add station coordinates to picks."""
        return picks.merge(
            stations[["id", "longitude", "latitude", "x_km", "y_km", "z_km"]].rename(columns={"id": "station_id"}),
            on="station_id",
            how="left"
        )
        
    def _run_gamma(self, picks, stations, velocity_model, method, use_amplitude):
        """
        Run GaMMA association (placeholder implementation).
        """
        # Placeholder implementation
        import numpy as np
        from datetime import datetime
        
        # Group picks by time windows to simulate events
        picks["phase_time"] = pd.to_datetime(picks["phase_time"])
        picks = picks.sort_values("phase_time")
        
        events = []
        associated_picks = []
        event_id = 0
        
        # Simple time-based clustering as placeholder
        time_threshold = pd.Timedelta(minutes=2)
        current_group = []
        last_time = None
        
        for _, pick in picks.iterrows():
            if last_time is None or (pick["phase_time"] - last_time) < time_threshold:
                current_group.append(pick)
            else:
                if len(current_group) >= 4:  # Minimum picks for an event
                    event, event_picks = self._create_event_from_picks(current_group, event_id)
                    events.append(event)
                    associated_picks.extend(event_picks)
                    event_id += 1
                current_group = [pick]
            last_time = pick["phase_time"]
            
        # Process last group
        if len(current_group) >= 4:
            event, event_picks = self._create_event_from_picks(current_group, event_id)
            events.append(event)
            associated_picks.extend(event_picks)
            
        return pd.DataFrame(events), pd.DataFrame(associated_picks)
        
    def _create_event_from_picks(self, picks, event_id):
        """Create event from group of picks."""
        import numpy as np
        
        # Calculate centroid
        lons = [p["longitude"] for p in picks]
        lats = [p["latitude"] for p in picks]
        times = [p["phase_time"] for p in picks]
        
        event = {
            "event_id": f"event_{event_id:06d}",
            "longitude": np.mean(lons),
            "latitude": np.mean(lats),
            "depth_km": np.random.uniform(5, 15),  # Random depth
            "origin_time": min(times).isoformat(),
            "magnitude": np.random.uniform(1.0, 4.0),  # Random magnitude
            "num_picks": len(picks)
        }
        
        # Transform coordinates
        event["x_km"], event["y_km"] = self.coord_transform.transform_coordinates(
            event["longitude"], event["latitude"]
        )
        event["z_km"] = event["depth_km"]
        
        # Assign event ID to picks
        event_picks = []
        for pick in picks:
            pick_dict = pick.to_dict()
            pick_dict["event_id"] = event["event_id"]
            event_picks.append(pick_dict)
            
        return event, event_picks


class AdlocProcessor(BaseProcessor):
    """
    ADLoc event location processor.
    """
    
    def __init__(self, config, region, protocol="file", token=None, root_path="./"):
        super().__init__(config, region, protocol, token, root_path)
        self.adloc_config = self.setup_processing_params("adloc")
        
    def locate_events(self, events_file, picks_file, stations_file, output_dir="locations"):
        """
        Relocate events using ADLoc.
        
        Args:
            events_file (str): Path to events file
            picks_file (str): Path to picks file
            stations_file (str): Path to stations file
            output_dir (str): Output directory for relocated events
            
        Returns:
            tuple: (relocated events DataFrame, refined picks DataFrame)
        """
        self.log_info("Starting ADLoc event relocation")
        
        # Load data
        events = self.load_events(events_file)
        picks = self.load_picks(picks_file)
        stations = self.load_stations(stations_file)
        
        # Setup ADLoc parameters
        velocity_model = self.get_velocity_model()
        method = self.adloc_config.get("method", "BFGS")
        use_amplitude = self.adloc_config.get("use_amplitude", True)
        use_station_term = self.adloc_config.get("use_station_term", True)
        
        self.log_info(f"Using method: {method}, station terms: {use_station_term}")
        
        # Run ADLoc relocation
        relocated_events, refined_picks = self._run_adloc(
            events, picks, stations, velocity_model, method, use_amplitude, use_station_term
        )
        
        # Save results
        events_path = f"{self.region}/{output_dir}/events_adloc.csv"
        picks_path = f"{self.region}/{output_dir}/picks_adloc.csv"
        
        self.save_results(relocated_events, events_path)
        self.save_results(refined_picks, picks_path)
        
        self.log_info(f"Completed ADLoc relocation. Processed {len(relocated_events)} events")
        return relocated_events, refined_picks
        
    def _run_adloc(self, events, picks, stations, velocity_model, method, use_amplitude, use_station_term):
        """
        Run ADLoc relocation (placeholder implementation).
        """
        # Placeholder implementation - add small random perturbations to simulate relocation
        import numpy as np
        
        relocated_events = events.copy()
        refined_picks = picks.copy()
        
        # Add small random perturbations to event locations
        relocated_events["longitude"] += np.random.normal(0, 0.001, len(events))
        relocated_events["latitude"] += np.random.normal(0, 0.001, len(events))
        relocated_events["depth_km"] += np.random.normal(0, 0.5, len(events))
        
        # Update transformed coordinates
        coords = self.coord_transform.transform_coordinates(
            relocated_events["longitude"], relocated_events["latitude"]
        )
        relocated_events["x_km"] = coords[0]
        relocated_events["y_km"] = coords[1]
        relocated_events["z_km"] = relocated_events["depth_km"]
        
        # Add relocation quality metrics
        relocated_events["rms_residual"] = np.random.uniform(0.1, 0.5, len(events))
        relocated_events["location_uncertainty"] = np.random.uniform(0.5, 2.0, len(events))
        relocated_events["magnitude_uncertainty"] = np.random.uniform(0.1, 0.3, len(events))
        
        # Add residuals to picks
        refined_picks["residual_time"] = np.random.normal(0, 0.2, len(picks))
        if use_amplitude:
            refined_picks["residual_amplitude"] = np.random.normal(0, 0.3, len(picks))
            
        return relocated_events, refined_picks
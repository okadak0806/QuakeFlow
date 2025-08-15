"""
Complete earthquake analysis workflow orchestration.
"""

import os
from pathlib import Path
from .config import RegionConfig
from .processors import PhaseNetProcessor, GammaProcessor, AdlocProcessor


class EarthquakeAnalysisWorkflow:
    """
    Complete earthquake analysis workflow orchestrator.
    """
    
    def __init__(self, region, config_path=None, protocol="file", token=None, root_path="./"):
        """
        Initialize workflow.
        
        Args:
            region (str): Region name
            config_path (str, optional): Path to configuration file
            protocol (str): File system protocol
            token (str, optional): Authentication token
            root_path (str): Root path for data
        """
        self.region = region
        self.protocol = protocol
        self.token = token
        self.root_path = root_path
        
        # Load configuration
        if config_path:
            self.config = RegionConfig.from_json(config_path)
        else:
            # Try to load default config for region
            default_config_path = f"configs/{region}.json"
            if os.path.exists(default_config_path):
                self.config = RegionConfig.from_json(default_config_path)
            else:
                self.config = RegionConfig(region)
                
        # Initialize processors
        self.phasenet = PhaseNetProcessor(
            self.config.get_config_dict(), region, protocol, token, root_path
        )
        self.gamma = GammaProcessor(
            self.config.get_config_dict(), region, protocol, token, root_path
        )
        self.adloc = AdlocProcessor(
            self.config.get_config_dict(), region, protocol, token, root_path
        )
        
    def run_full_workflow(self, waveform_dir, stations_file, output_base_dir="results"):
        """
        Run complete earthquake analysis workflow.
        
        Args:
            waveform_dir (str): Directory containing waveforms
            stations_file (str): Path to stations file
            output_base_dir (str): Base output directory
            
        Returns:
            dict: Results from each processing step
        """
        self.log_info("Starting complete earthquake analysis workflow")
        
        # Create output directories
        self._create_output_directories(output_base_dir)
        
        results = {}
        
        # Step 1: PhaseNet phase picking
        self.log_info("Step 1: Running PhaseNet phase picking")
        picks = self.phasenet.process_waveforms(
            waveform_dir, 
            stations_file, 
            f"{output_base_dir}/picks"
        )
        results["picks"] = picks
        
        # Step 2: GaMMA event association
        self.log_info("Step 2: Running GaMMA event association")
        picks_file = f"{self.region}/{output_base_dir}/picks/picks_phasenet.csv"
        events, associated_picks = self.gamma.associate_events(
            picks_file,
            stations_file,
            f"{output_base_dir}/events"
        )
        results["events"] = events
        results["associated_picks"] = associated_picks
        
        # Step 3: ADLoc event location
        self.log_info("Step 3: Running ADLoc event relocation")
        events_file = f"{self.region}/{output_base_dir}/events/events_gamma.csv"
        picks_file = f"{self.region}/{output_base_dir}/events/picks_gamma.csv"
        relocated_events, refined_picks = self.adloc.locate_events(
            events_file,
            picks_file,
            stations_file,
            f"{output_base_dir}/locations"
        )
        results["relocated_events"] = relocated_events
        results["refined_picks"] = refined_picks
        
        self.log_info("Completed full earthquake analysis workflow")
        return results
        
    def run_phasenet_only(self, waveform_dir, stations_file, output_dir="picks"):
        """
        Run only PhaseNet phase picking.
        
        Args:
            waveform_dir (str): Directory containing waveforms
            stations_file (str): Path to stations file
            output_dir (str): Output directory
            
        Returns:
            pd.DataFrame: Detected picks
        """
        self.log_info("Running PhaseNet phase picking only")
        return self.phasenet.process_waveforms(waveform_dir, stations_file, output_dir)
        
    def run_gamma_only(self, picks_file, stations_file, output_dir="events"):
        """
        Run only GaMMA event association.
        
        Args:
            picks_file (str): Path to picks file
            stations_file (str): Path to stations file
            output_dir (str): Output directory
            
        Returns:
            tuple: (events DataFrame, associated picks DataFrame)
        """
        self.log_info("Running GaMMA event association only")
        return self.gamma.associate_events(picks_file, stations_file, output_dir)
        
    def run_adloc_only(self, events_file, picks_file, stations_file, output_dir="locations"):
        """
        Run only ADLoc event location.
        
        Args:
            events_file (str): Path to events file
            picks_file (str): Path to picks file
            stations_file (str): Path to stations file
            output_dir (str): Output directory
            
        Returns:
            tuple: (relocated events DataFrame, refined picks DataFrame)
        """
        self.log_info("Running ADLoc event relocation only")
        return self.adloc.locate_events(events_file, picks_file, stations_file, output_dir)
        
    def run_partial_workflow(self, start_step="phasenet", end_step="adloc", **kwargs):
        """
        Run partial workflow from start_step to end_step.
        
        Args:
            start_step (str): Starting step ("phasenet", "gamma", "adloc")
            end_step (str): Ending step ("phasenet", "gamma", "adloc")
            **kwargs: Arguments for workflow steps
            
        Returns:
            dict: Results from processing steps
        """
        steps = ["phasenet", "gamma", "adloc"]
        start_idx = steps.index(start_step)
        end_idx = steps.index(end_step)
        
        if start_idx > end_idx:
            raise ValueError("start_step must come before end_step")
            
        results = {}
        
        if start_idx <= 0 <= end_idx:  # Run PhaseNet
            picks = self.run_phasenet_only(
                kwargs["waveform_dir"],
                kwargs["stations_file"],
                kwargs.get("picks_output_dir", "picks")
            )
            results["picks"] = picks
            
        if start_idx <= 1 <= end_idx:  # Run GaMMA
            picks_file = kwargs.get("picks_file", f"{self.region}/picks/picks_phasenet.csv")
            events, associated_picks = self.run_gamma_only(
                picks_file,
                kwargs["stations_file"],
                kwargs.get("events_output_dir", "events")
            )
            results["events"] = events
            results["associated_picks"] = associated_picks
            
        if start_idx <= 2 <= end_idx:  # Run ADLoc
            events_file = kwargs.get("events_file", f"{self.region}/events/events_gamma.csv")
            picks_file = kwargs.get("picks_file", f"{self.region}/events/picks_gamma.csv")
            relocated_events, refined_picks = self.run_adloc_only(
                events_file,
                picks_file,
                kwargs["stations_file"],
                kwargs.get("locations_output_dir", "locations")
            )
            results["relocated_events"] = relocated_events
            results["refined_picks"] = refined_picks
            
        return results
        
    def _create_output_directories(self, base_dir):
        """Create output directory structure."""
        dirs = [
            f"{self.region}/{base_dir}",
            f"{self.region}/{base_dir}/picks",
            f"{self.region}/{base_dir}/events", 
            f"{self.region}/{base_dir}/locations",
            f"{self.region}/{base_dir}/figures"
        ]
        
        for dir_path in dirs:
            if self.protocol == "file":
                Path(f"{self.root_path}/{dir_path}").mkdir(parents=True, exist_ok=True)
                
    def get_config(self):
        """Get current configuration."""
        return self.config
        
    def update_config(self, config_updates):
        """
        Update configuration.
        
        Args:
            config_updates (dict): Configuration updates to merge
        """
        self.config.merge_config(config_updates)
        
        # Reinitialize processors with updated config
        config_dict = self.config.get_config_dict()
        self.phasenet = PhaseNetProcessor(
            config_dict, self.region, self.protocol, self.token, self.root_path
        )
        self.gamma = GammaProcessor(
            config_dict, self.region, self.protocol, self.token, self.root_path
        )
        self.adloc = AdlocProcessor(
            config_dict, self.region, self.protocol, self.token, self.root_path
        )
        
    def log_info(self, message):
        """Log information message."""
        print(f"[{self.region.upper()} WORKFLOW] {message}")
        
    def get_summary_stats(self, results):
        """
        Get summary statistics from workflow results.
        
        Args:
            results (dict): Results from workflow execution
            
        Returns:
            dict: Summary statistics
        """
        stats = {
            "region": self.region,
            "workflow_completed": True
        }
        
        if "picks" in results:
            picks = results["picks"]
            stats["total_picks"] = len(picks)
            stats["p_picks"] = len(picks[picks["phase_type"] == "P"])
            stats["s_picks"] = len(picks[picks["phase_type"] == "S"])
            
        if "events" in results:
            events = results["events"]
            stats["total_events"] = len(events)
            if "magnitude" in events.columns:
                stats["magnitude_range"] = [
                    events["magnitude"].min(), 
                    events["magnitude"].max()
                ]
                
        if "relocated_events" in results:
            relocated = results["relocated_events"]
            stats["relocated_events"] = len(relocated)
            if "rms_residual" in relocated.columns:
                stats["mean_rms_residual"] = relocated["rms_residual"].mean()
                
        return stats
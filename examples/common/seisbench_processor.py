"""
SeisbenchPhaseNet processor for QuakeFlow.

This module provides integration with SeisBench PyTorch-based PhaseNet models
for earthquake phase picking, including support for fine-tuning on Japanese data.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    import seisbench
    import seisbench.models as sbm
    import seisbench.data as sbd
    import seisbench.generate as sbg
    from seisbench.util import worker_seeding
    HAS_SEISBENCH = True
except ImportError:
    HAS_SEISBENCH = False
    print("⚠️ Warning: SeisBench not available. Install with: pip install seisbench")

import obspy
from obspy import Stream, Trace, UTCDateTime

from .base_processor import BaseProcessor
from .config import RegionConfig
from .data_io import DataIO


class SeisbenchPhaseNetProcessor(BaseProcessor):
    """
    PyTorch-based PhaseNet processor using SeisBench.
    
    Supports:
    - Pre-trained PhaseNet models from SeisBench
    - Fine-tuning on Japanese earthquake data
    - Efficient batch processing with GPU acceleration
    - Advanced preprocessing and augmentation
    """
    
    def __init__(self, 
                 config: RegionConfig,
                 protocol: str = "file", 
                 token: Optional[str] = None, 
                 root_path: str = "./"):
        """
        Initialize SeisbenchPhaseNet processor.
        
        Args:
            config (RegionConfig): Region configuration
            protocol (str): File protocol (file, gs, s3)
            token (str, optional): Authentication token
            root_path (str): Root path for file operations
        """
        super().__init__(config, protocol, token, root_path)
        
        if not HAS_SEISBENCH:
            raise ImportError("SeisBench is required but not installed. Install with: pip install seisbench")
        
        # Initialize model parameters
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = config.config.get('processing', {}).get('phasenet', {}).get('model', 'phasenet')
        self.batch_size = config.config.get('processing', {}).get('phasenet', {}).get('batch_size', 32)
        
        # Phase detection thresholds
        self.threshold_p = config.config.get('processing', {}).get('phasenet', {}).get('threshold_p', 0.3)
        self.threshold_s = config.config.get('processing', {}).get('phasenet', {}).get('threshold_s', 0.3)
        
        # Preprocessing parameters
        self.sampling_rate = config.config.get('processing', {}).get('phasenet', {}).get('sampling_rate', 100)
        self.window_length_sec = config.config.get('processing', {}).get('phasenet', {}).get('window_length', 30.01)
        self.overlap_sec = config.config.get('processing', {}).get('phasenet', {}).get('overlap', 20)
        
        # Japanese-specific settings
        self.japan_specific = config.config.get('processing', {}).get('phasenet', {}).get('japan_specific', False)
        
        print(f"🧠 SeisbenchPhaseNet Processor initialized")
        print(f"   Model: {self.model_name}")
        print(f"   Device: {self.device}")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Japan-specific: {self.japan_specific}")
    
    def load_model(self, model_path: Optional[str] = None, 
                  pretrained: bool = True,
                  force_reload: bool = False) -> None:
        """
        Load SeisbenchPhaseNet model.
        
        Args:
            model_path (str, optional): Path to custom model weights
            pretrained (bool): Use pre-trained weights from SeisBench
            force_reload (bool): Force model reload even if already loaded
        """
        if self.model is not None and not force_reload:
            print("Model already loaded. Use force_reload=True to reload.")
            return
        
        print(f"🔄 Loading SeisbenchPhaseNet model...")
        
        try:
            if model_path and os.path.exists(model_path):
                # Load custom model
                print(f"   Loading custom model from: {model_path}")
                if model_path.endswith('.pt') or model_path.endswith('.pth'):
                    # PyTorch checkpoint
                    self.model = sbm.PhaseNet(pretrained=False)
                    checkpoint = torch.load(model_path, map_location=self.device)
                    self.model.load_state_dict(checkpoint['model_state_dict'] if 'model_state_dict' in checkpoint else checkpoint)
                else:
                    # SeisBench model format
                    self.model = sbm.PhaseNet.from_pretrained(model_path)
            else:
                # Load pre-trained model from SeisBench
                if self.japan_specific:
                    # Try Japan-specific model first
                    try:
                        print("   Attempting to load Japan-specific PhaseNet model...")
                        self.model = sbm.PhaseNet.from_pretrained("jma")  # Japan-specific model
                        print("   ✅ Japan-specific (JMA) PhaseNet model loaded")
                    except:
                        print("   Loading original PhaseNet model...")
                        self.model = sbm.PhaseNet.from_pretrained("original")
                else:
                    # Load standard model
                    model_variants = {
                        'phasenet': 'original',
                        'phasenet_original': 'original',
                        'phasenet_japan': 'jma',
                        'phasenet_stead': 'stead',
                        'phasenet_scedc': 'scedc',
                        'phasenet_ethz': 'ethz'
                    }
                    
                    model_key = model_variants.get(self.model_name, 'original')
                    print(f"   Loading {model_key} from SeisBench...")
                    self.model = sbm.PhaseNet.from_pretrained(model_key)
            
            # Move model to device
            self.model = self.model.to(self.device)
            self.model.eval()
            
            print(f"✅ Model loaded successfully")
            print(f"   Model type: {type(self.model).__name__}")
            print(f"   Device: {next(self.model.parameters()).device}")
            print(f"   Parameters: {sum(p.numel() for p in self.model.parameters()):,}")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise
    
    def preprocess_stream(self, stream: Stream, 
                         start_time: Optional[UTCDateTime] = None,
                         end_time: Optional[UTCDateTime] = None) -> List[np.ndarray]:
        """
        Preprocess ObsPy stream for SeisbenchPhaseNet.
        
        Args:
            stream (Stream): ObsPy stream
            start_time (UTCDateTime, optional): Start time for processing
            end_time (UTCDateTime, optional): End time for processing
            
        Returns:
            List[np.ndarray]: List of preprocessed windows
        """
        print(f"🔄 Preprocessing stream for SeisbenchPhaseNet...")
        
        # Basic stream processing
        stream_copy = stream.copy()
        
        # Remove response and filter if specified
        preprocessing_config = self.config.config.get('processing', {}).get('phasenet', {}).get('preprocessing', {})
        
        if preprocessing_config.get('detrend', True):
            stream_copy.detrend('demean')
            
        if preprocessing_config.get('taper', False):
            taper_fraction = preprocessing_config.get('taper', 0.05)
            stream_copy.taper(max_percentage=taper_fraction)
        
        if 'filter' in preprocessing_config:
            filter_config = preprocessing_config['filter']
            if filter_config['type'] == 'bandpass':
                stream_copy.filter(
                    'bandpass',
                    freqmin=filter_config['freqmin'],
                    freqmax=filter_config['freqmax']
                )
        
        # Resample to target sampling rate
        for trace in stream_copy:
            if trace.stats.sampling_rate != self.sampling_rate:
                trace.resample(self.sampling_rate)
        
        # Organize by station
        stations = {}
        for trace in stream_copy:
            station_id = f"{trace.stats.network}.{trace.stats.station}"
            if station_id not in stations:
                stations[station_id] = []
            stations[station_id].append(trace)
        
        # Create 3-component windows
        windows = []
        window_metadata = []
        
        window_samples = int(self.window_length_sec * self.sampling_rate)
        overlap_samples = int(self.overlap_sec * self.sampling_rate)
        step_samples = window_samples - overlap_samples
        
        for station_id, traces in stations.items():
            if len(traces) < 3:
                print(f"   ⚠️ Skipping {station_id}: insufficient components ({len(traces)})")
                continue
            
            # Sort traces by component (Z, N, E)
            component_map = {}
            for trace in traces:
                component = trace.stats.channel[-1].upper()
                component_map[component] = trace
            
            # Try to get Z, N, E components
            component_order = ['Z', 'N', 'E']
            if not all(comp in component_map for comp in component_order):
                # Try alternative component naming
                alt_order = ['Z', '1', '2']
                if all(comp in component_map for comp in alt_order):
                    component_order = alt_order
                else:
                    print(f"   ⚠️ Skipping {station_id}: missing required components")
                    continue
            
            # Get time range
            min_start = max(trace.stats.starttime for trace in traces)
            max_end = min(trace.stats.endtime for trace in traces)
            
            if start_time:
                min_start = max(min_start, start_time)
            if end_time:
                max_end = min(max_end, end_time)
            
            if max_end - min_start < self.window_length_sec:
                print(f"   ⚠️ Skipping {station_id}: insufficient data length")
                continue
            
            # Create sliding windows
            current_time = min_start
            while current_time + self.window_length_sec <= max_end:
                try:
                    # Extract 3-component data for this window
                    window_data = np.zeros((3, window_samples))
                    
                    for i, comp in enumerate(component_order):
                        trace = component_map[comp]
                        # Use slice with nearest_sample=False to get exact samples
                        trace_slice = trace.slice(current_time, current_time + self.window_length_sec, nearest_sample=False)
                        
                        # Ensure we have exactly the right number of samples
                        if len(trace_slice.data) >= window_samples:
                            # Take exactly window_samples
                            data = trace_slice.data[:window_samples].astype(np.float32)
                            # Normalize trace
                            if np.std(data) > 0:
                                data = (data - np.mean(data)) / np.std(data)
                            window_data[i, :] = data
                        elif len(trace_slice.data) == window_samples - 1:
                            # Handle off-by-one due to floating point precision
                            data = trace_slice.data.astype(np.float32)
                            # Pad with last sample
                            data = np.append(data, data[-1])
                            if np.std(data) > 0:
                                data = (data - np.mean(data)) / np.std(data)
                            window_data[i, :] = data
                    
                    # Check for valid data
                    if not np.any(np.isnan(window_data)) and np.any(np.abs(window_data) > 1e-10):
                        windows.append(window_data)
                        window_metadata.append({
                            'station': station_id,
                            'start_time': current_time,
                            'end_time': current_time + self.window_length_sec,
                            'sampling_rate': self.sampling_rate,
                            'components': component_order
                        })
                
                except Exception as e:
                    print(f"   ⚠️ Error processing window for {station_id}: {e}")
                
                current_time += step_samples / self.sampling_rate
        
        print(f"✅ Preprocessed {len(windows)} windows from {len(stations)} stations")
        self.window_metadata = window_metadata
        
        return windows
    
    def predict_batch(self, windows: List[np.ndarray]) -> Dict[str, np.ndarray]:
        """
        Run batch prediction on preprocessed windows.
        
        Args:
            windows (List[np.ndarray]): List of preprocessed windows
            
        Returns:
            Dict[str, np.ndarray]: Predictions with P and S phase probabilities
        """
        if self.model is None:
            self.load_model()
        
        print(f"🔮 Running SeisbenchPhaseNet predictions on {len(windows)} windows...")
        
        all_predictions = []
        
        # Process in batches
        for i in range(0, len(windows), self.batch_size):
            batch_windows = windows[i:i + self.batch_size]
            batch_tensor = torch.tensor(np.array(batch_windows), dtype=torch.float32).to(self.device)
            
            with torch.no_grad():
                predictions = self.model(batch_tensor)
                
                # Convert to numpy
                if isinstance(predictions, tuple):
                    # Some models return tuple (P, S, N) probabilities
                    p_pred = predictions[0].cpu().numpy()
                    s_pred = predictions[1].cpu().numpy()
                else:
                    # Standard format: [batch, 3, samples] where 3 = [P, S, Noise]
                    p_pred = predictions[:, 0, :].cpu().numpy()
                    s_pred = predictions[:, 1, :].cpu().numpy()
                
                all_predictions.append({
                    'P': p_pred,
                    'S': s_pred
                })
        
        # Concatenate all predictions
        final_predictions = {
            'P': np.concatenate([pred['P'] for pred in all_predictions], axis=0),
            'S': np.concatenate([pred['S'] for pred in all_predictions], axis=0)
        }
        
        print(f"✅ Predictions completed")
        print(f"   P predictions shape: {final_predictions['P'].shape}")
        print(f"   S predictions shape: {final_predictions['S'].shape}")
        
        return final_predictions
    
    def extract_picks(self, predictions: Dict[str, np.ndarray]) -> pd.DataFrame:
        """
        Extract phase picks from predictions.
        
        Args:
            predictions (Dict[str, np.ndarray]): Model predictions
            
        Returns:
            pd.DataFrame: Extracted picks
        """
        print(f"📍 Extracting phase picks with thresholds P={self.threshold_p}, S={self.threshold_s}...")
        
        picks = []
        
        for i, metadata in enumerate(self.window_metadata):
            p_probs = predictions['P'][i]
            s_probs = predictions['S'][i]
            
            # Find peaks above threshold
            p_peaks = self._find_peaks(p_probs, self.threshold_p)
            s_peaks = self._find_peaks(s_probs, self.threshold_s)
            
            # Convert sample indices to absolute times
            start_time = metadata['start_time']
            
            for peak_idx in p_peaks:
                pick_time = start_time + peak_idx / self.sampling_rate
                picks.append({
                    'station': metadata['station'],
                    'phase': 'P',
                    'time': pick_time.isoformat(),
                    'probability': float(p_probs[peak_idx]),
                    'window_start': start_time.isoformat(),
                    'sample_index': int(peak_idx)
                })
            
            for peak_idx in s_peaks:
                pick_time = start_time + peak_idx / self.sampling_rate
                picks.append({
                    'station': metadata['station'],
                    'phase': 'S', 
                    'time': pick_time.isoformat(),
                    'probability': float(s_probs[peak_idx]),
                    'window_start': start_time.isoformat(),
                    'sample_index': int(peak_idx)
                })
        
        picks_df = pd.DataFrame(picks)
        
        if len(picks_df) > 0:
            # Remove duplicate picks (same station, phase, similar time)
            picks_df = self._remove_duplicate_picks(picks_df)
            
            # Sort by time
            picks_df = picks_df.sort_values('time').reset_index(drop=True)
        
        print(f"✅ Extracted {len(picks_df)} picks")
        if len(picks_df) > 0:
            p_count = len(picks_df[picks_df['phase'] == 'P'])
            s_count = len(picks_df[picks_df['phase'] == 'S'])
            print(f"   P-picks: {p_count}, S-picks: {s_count}")
        
        return picks_df
    
    def _find_peaks(self, probabilities: np.ndarray, threshold: float) -> List[int]:
        """Find peaks in probability array above threshold."""
        from scipy.signal import find_peaks
        
        peaks, properties = find_peaks(
            probabilities, 
            height=threshold,
            distance=int(0.5 * self.sampling_rate),  # Minimum 0.5 seconds between peaks
            prominence=0.1
        )
        
        return peaks.tolist()
    
    def _remove_duplicate_picks(self, picks_df: pd.DataFrame, time_tolerance: float = 1.0) -> pd.DataFrame:
        """Remove duplicate picks within time tolerance."""
        if len(picks_df) == 0:
            return picks_df
        
        picks_df['datetime'] = pd.to_datetime(picks_df['time'])
        picks_df = picks_df.sort_values(['station', 'phase', 'datetime'])
        
        keep_indices = []
        
        for (station, phase), group in picks_df.groupby(['station', 'phase']):
            if len(group) == 1:
                keep_indices.extend(group.index.tolist())
            else:
                # Keep highest probability pick within time windows
                group = group.sort_values('datetime')
                current_idx = group.index[0]
                keep_indices.append(current_idx)
                
                for idx in group.index[1:]:
                    time_diff = (group.loc[idx, 'datetime'] - group.loc[current_idx, 'datetime']).total_seconds()
                    
                    if time_diff > time_tolerance:
                        current_idx = idx
                        keep_indices.append(current_idx)
                    elif group.loc[idx, 'probability'] > group.loc[current_idx, 'probability']:
                        # Replace with higher probability pick
                        keep_indices.remove(current_idx)
                        current_idx = idx
                        keep_indices.append(current_idx)
        
        return picks_df.loc[keep_indices].drop('datetime', axis=1).reset_index(drop=True)
    
    def process_waveforms(self, waveform_dir: str, 
                         stations_file: str,
                         output_dir: str = "phasenet_seisbench",
                         start_time: Optional[str] = None,
                         end_time: Optional[str] = None) -> pd.DataFrame:
        """
        Process waveforms with SeisbenchPhaseNet.
        
        Args:
            waveform_dir (str): Directory containing waveform files
            stations_file (str): Station information file
            output_dir (str): Output directory for results
            start_time (str, optional): Start time for processing
            end_time (str, optional): End time for processing
            
        Returns:
            pd.DataFrame: Phase picks
        """
        print(f"🌊 Processing waveforms with SeisbenchPhaseNet...")
        print(f"   Waveform dir: {waveform_dir}")
        print(f"   Stations file: {stations_file}")
        print(f"   Output dir: {output_dir}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Load stations
        stations_df = self.data_io.load_csv(stations_file) if stations_file.endswith('.csv') else self.load_stations_json(stations_file)
        print(f"   Loaded {len(stations_df)} stations")
        
        # Load waveforms
        stream = self.load_waveforms_from_directory(waveform_dir)
        print(f"   Loaded {len(stream)} traces")
        
        if len(stream) == 0:
            print("⚠️ No waveforms found")
            return pd.DataFrame()
        
        # Convert time strings
        start_utc = UTCDateTime(start_time) if start_time else None
        end_utc = UTCDateTime(end_time) if end_time else None
        
        # Preprocess waveforms
        windows = self.preprocess_stream(stream, start_utc, end_utc)
        
        if len(windows) == 0:
            print("⚠️ No valid windows created")
            return pd.DataFrame()
        
        # Run predictions
        predictions = self.predict_batch(windows)
        
        # Extract picks
        picks_df = self.extract_picks(predictions)
        
        # Save results
        if len(picks_df) > 0:
            picks_path = os.path.join(output_dir, 'picks_seisbench.csv')
            self.data_io.save_csv(picks_df, picks_path)
            print(f"💾 Picks saved: {picks_path}")
            
            # Save processing summary
            summary = {
                'model_name': self.model_name,
                'total_windows': len(windows),
                'total_picks': len(picks_df),
                'p_picks': len(picks_df[picks_df['phase'] == 'P']),
                's_picks': len(picks_df[picks_df['phase'] == 'S']),
                'processing_time': datetime.now().isoformat(),
                'thresholds': {
                    'P': self.threshold_p,
                    'S': self.threshold_s
                },
                'device': str(self.device),
                'batch_size': self.batch_size
            }
            
            summary_path = os.path.join(output_dir, 'processing_summary.json')
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"📊 Summary saved: {summary_path}")
        
        return picks_df
    
    def fine_tune_model(self, 
                       training_data_path: str,
                       output_model_path: str,
                       epochs: int = 10,
                       learning_rate: float = 1e-4,
                       validation_split: float = 0.2) -> Dict[str, Any]:
        """
        Fine-tune SeisbenchPhaseNet model on Japanese data.
        
        Args:
            training_data_path (str): Path to training data
            output_model_path (str): Path to save fine-tuned model
            epochs (int): Number of training epochs
            learning_rate (float): Learning rate for training
            validation_split (float): Fraction of data for validation
            
        Returns:
            Dict[str, Any]: Training results and metrics
        """
        print(f"🎯 Fine-tuning SeisbenchPhaseNet model...")
        print(f"   Training data: {training_data_path}")
        print(f"   Output model: {output_model_path}")
        print(f"   Epochs: {epochs}")
        print(f"   Learning rate: {learning_rate}")
        
        if self.model is None:
            self.load_model(pretrained=True)
        
        # Load training data (implementation depends on data format)
        # This is a placeholder - actual implementation would depend on your data format
        print("⚠️ Fine-tuning implementation depends on specific training data format")
        print("   Please implement data loading for your specific Japanese dataset")
        
        # Setup training
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.BCELoss()
        
        training_results = {
            'status': 'placeholder',
            'message': 'Fine-tuning implementation needs to be completed with actual training data',
            'epochs_planned': epochs,
            'learning_rate': learning_rate
        }
        
        print(f"📝 Fine-tuning setup complete - implementation needed for specific data format")
        
        return training_results
    
    def load_waveforms_from_directory(self, waveform_dir: str) -> Stream:
        """Load waveforms from directory."""
        stream = Stream()
        
        for file_path in Path(waveform_dir).glob("**/*"):
            if file_path.suffix.lower() in ['.mseed', '.sac', '.seed']:
                try:
                    stream += obspy.read(str(file_path))
                except Exception as e:
                    print(f"   ⚠️ Error reading {file_path}: {e}")
        
        return stream
    
    def load_stations_json(self, stations_file: str) -> pd.DataFrame:
        """Load stations from JSON file."""
        with open(stations_file, 'r') as f:
            stations_data = json.load(f)
        
        # Convert to DataFrame (format may vary)
        if isinstance(stations_data, list):
            return pd.DataFrame(stations_data)
        elif isinstance(stations_data, dict):
            # Handle different JSON structures
            if 'stations' in stations_data:
                return pd.DataFrame(stations_data['stations'])
            else:
                return pd.DataFrame([stations_data])
        else:
            raise ValueError(f"Unsupported stations file format: {type(stations_data)}")
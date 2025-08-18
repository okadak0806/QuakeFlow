# QuakeFlow Examples - Refactored Earthquake Analysis Workflows

This directory contains refactored and standardized examples for earthquake data processing using the QuakeFlow framework. The examples demonstrate how to perform complete earthquake analysis workflows including phase picking, event association, and event location across different regions.

## 🔧 Refactoring Summary

This directory has been **completely refactored** to eliminate code duplication and improve maintainability:

### Before Refactoring:
- ❌ 70% code duplication across regions
- ❌ Inconsistent naming conventions
- ❌ Scattered utility functions
- ❌ Region-specific hardcoded parameters
- ❌ Difficult to maintain and extend

### After Refactoring:
- ✅ Unified common utilities and base classes
- ✅ Standardized configuration management
- ✅ Consistent API across all regions
- ✅ Modular processor architecture
- ✅ Easy to add new regions and customize workflows

## 📁 Directory Structure

```
examples/
├── common/                     # Shared utilities and base classes
│   ├── __init__.py
│   ├── base_processor.py      # Base processor class
│   ├── config.py              # Configuration management
│   ├── coordinates.py         # Coordinate transformations
│   ├── data_io.py             # File I/O utilities
│   ├── velocity_models.py     # Velocity model management
│   ├── processors.py          # PhaseNet, GaMMA, ADLoc processors
│   ├── workflow.py            # Complete workflow orchestration
│   └── cli.py                 # Command line interface utilities
├── configs/                    # Standardized region configurations
│   ├── california.json
│   ├── japan.json
│   ├── hawaii.json
│   ├── forge.json
│   └── seafoam.json
├── templates/                  # Unified script templates
│   ├── run_phasenet.py        # PhaseNet phase picking
│   ├── run_gamma.py           # GaMMA event association
│   ├── run_adloc.py           # ADLoc event location
│   └── run_workflow.py        # Complete workflow
├── california/                 # Region-specific examples (legacy)
├── japan/                     # Region-specific examples (legacy)
├── hawaii/                    # Region-specific examples (legacy)
├── forge/                     # Region-specific examples (legacy)
├── seafoam/                   # Region-specific examples (legacy)
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Complete Workflow (Recommended)

Run the entire earthquake analysis pipeline with a single command:

```bash
# California example
python templates/run_workflow.py \
    --region california \
    --waveform_dir /path/to/waveforms \
    --stations_file /path/to/stations.json \
    --output_dir results

# Japan example with custom config
python templates/run_workflow.py \
    --region japan \
    --config configs/japan.json \
    --waveform_dir /path/to/waveforms \
    --stations_file /path/to/stations.json \
    --output_dir results
```

### 2. Individual Processing Steps

Run individual components of the workflow:

```bash
# PhaseNet phase picking only
python templates/run_phasenet.py \
    --region california \
    --waveform_dir /path/to/waveforms \
    --stations_file /path/to/stations.json

# GaMMA event association only
python templates/run_gamma.py \
    --region california \
    --picks_file picks/picks_phasenet.csv \
    --stations_file /path/to/stations.json

# ADLoc event location only
python templates/run_adloc.py \
    --region california \
    --events_file events/events_gamma.csv \
    --picks_file events/picks_gamma.csv \
    --stations_file /path/to/stations.json
```

### 3. Using Python API

For programmatic access, use the workflow classes directly:

```python
from common import EarthquakeAnalysisWorkflow

# Initialize workflow
workflow = EarthquakeAnalysisWorkflow(
    region="california",
    config_path="configs/california.json"
)

# Run complete workflow
results = workflow.run_full_workflow(
    waveform_dir="/path/to/waveforms",
    stations_file="/path/to/stations.json",
    output_base_dir="results"
)

# Access results
picks = results["picks"]
events = results["relocated_events"]
```

## ⚙️ Configuration Management

### Standardized Configuration Format

All regions now use a standardized JSON configuration format:

```json
{
  "region": "california",
  "description": "Standard configuration for California",
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
    "phasenet": { "threshold_p": 0.3, "threshold_s": 0.3 },
    "gamma": { "method": "BGMM", "use_amplitude": true },
    "adloc": { "method": "BFGS", "use_station_term": true }
  }
}
```

### Available Regions

Pre-configured regions with optimized parameters:

- **california**: NCEDC-based configuration for California
- **japan**: Hi-net/JMA-based configuration for Japan
- **hawaii**: HVO-based configuration for Hawaiian volcanoes
- **forge**: Configuration for FORGE geothermal field
- **seafoam**: Configuration for ocean bottom seismology

### Custom Configurations

Create custom configurations by modifying existing ones:

```python
from common import RegionConfig

# Load and modify existing config
config = RegionConfig.from_json("configs/california.json")
config.update_bounds(32.0, 35.0, -120.0, -115.0)  # Southern California
config.update_processing_param("phasenet", "threshold_p", 0.25)
config.save_json("configs/socal_custom.json")
```

## 🔧 Common Utilities Overview

### BaseProcessor
- Unified base class for all processors
- Common data loading and coordinate transformation
- Standardized file I/O operations

### RegionConfig
- Centralized configuration management
- Validation and default value handling
- Support for custom configurations

### CoordinateTransform
- Automatic projection setup based on region bounds
- Station and event coordinate transformation
- Distance calculations

### VelocityModel
- Support for simple and layered 1D models
- Integration with GaMMA and ADLoc
- Pre-defined models for common regions

### DataIO
- Multi-protocol file system support (local, cloud storage)
- Unified CSV, JSON, Parquet handling
- Automatic directory creation

## 🌍 Supported Regions and Data Sources

| Region | Data Provider | Velocity Model | Typical Use Case |
|--------|---------------|----------------|------------------|
| California | NCEDC | Layered 1D | Regional seismicity |
| Japan | Hi-net/JMA | Layered 1D | Subduction zone earthquakes |
| Hawaii | HVO | Simple | Volcanic earthquakes |
| FORGE | FORGE | Simple | Induced seismicity |
| Seafoam | OOI | Marine layered | Ocean bottom seismology |

## 📊 Output Structure

The unified workflow creates a consistent output structure:

```
results/
├── picks/
│   └── picks_phasenet.csv      # PhaseNet picks
├── events/
│   ├── events_gamma.csv        # GaMMA events
│   └── picks_gamma.csv         # Associated picks
├── locations/
│   ├── events_adloc.csv        # Relocated events
│   └── picks_adloc.csv         # Refined picks
└── figures/                    # Visualization outputs
    ├── events_map.png
    ├── magnitude_histogram.png
    └── residual_plots.png
```

## 🔄 Migration from Legacy Scripts

### For Existing Users

If you have existing scripts using the old region-specific approach:

1. **Keep using existing scripts** - They still work but are no longer maintained
2. **Migrate gradually** - Use the new templates as starting points
3. **Customize configurations** - Create region-specific JSON configs

### Migration Example

Old approach (california/run_phasenet.py):
```python
# Hardcoded parameters scattered throughout
config["minlatitude"] = 32.0
config["maxlatitude"] = 43.0
# ... lots of duplicate code
```

New approach (templates/run_phasenet.py):
```python
# Clean, unified interface
workflow = EarthquakeAnalysisWorkflow(region="california")
picks = workflow.run_phasenet_only(waveform_dir, stations_file)
```

## 🔬 Advanced Usage

### Custom Processors

Extend the base processor for specialized workflows:

```python
from common import BaseProcessor

class CustomProcessor(BaseProcessor):
    def custom_analysis(self, data):
        # Your custom processing logic
        return processed_data
```

### Distributed Processing

Use the node/rank parameters for parallel processing:

```bash
# Node 0 of 4
python templates/run_workflow.py \
    --region california \
    --num_nodes 4 \
    --node_rank 0 \
    --waveform_dir /path/to/waveforms \
    --stations_file /path/to/stations.json
```

### Cloud Storage Integration

Process data from cloud storage:

```bash
python templates/run_workflow.py \
    --region california \
    --protocol gs \
    --token /path/to/gcs-key.json \
    --root_path gs://my-bucket \
    --waveform_dir waveforms/ \
    --stations_file stations.json
```

## 🐛 Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're running scripts from the correct directory
2. **Missing configurations**: Check that the region config file exists
3. **File not found**: Verify file paths are correct for your protocol
4. **Coordinate transformation issues**: Check geographic bounds in config

### Getting Help

1. Check the existing regional examples for reference implementations
2. Review the configuration files for parameter explanations
3. Use the `--verbose` or `--debug` flags for detailed logging
4. Examine the common utilities source code for advanced customization

## 🤝 Contributing

When adding new regions or features:

1. Create a standardized configuration file in `configs/`
2. Test with the unified script templates
3. Add any region-specific processors to `common/processors.py`
4. Update this README with new region information

## 📈 Performance Improvements

The refactored codebase provides several performance benefits:

- **Reduced memory usage**: Eliminated duplicate imports and data loading
- **Faster startup**: Shared module loading and configuration caching
- **Better scalability**: Unified parallel processing support
- **Improved error handling**: Consistent validation and error reporting

## 📝 License

This refactored code maintains compatibility with the original QuakeFlow license. See the main project LICENSE file for details.
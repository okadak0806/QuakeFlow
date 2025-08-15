#!/bin/bash
# Enhanced startup script for QuakeFlow runtime environment

set -e

echo "Starting QuakeFlow Enhanced Runtime Environment..."

# Set up environment variables
export QUAKEFLOW_HOME="/opt/quakeflow"
export PYTHONPATH="${QUAKEFLOW_HOME}:${PYTHONPATH}"

# Create necessary directories
mkdir -p /home/jovyan/work/{config,data,results,logs}
mkdir -p /home/jovyan/work/results/{picks,events,locations,figures}

# Set up logging
LOG_DIR="/home/jovyan/work/logs"
mkdir -p $LOG_DIR
export QUAKEFLOW_LOG_DIR=$LOG_DIR

# Initialize QuakeFlow configuration
echo "Initializing QuakeFlow configuration..."
cat > /home/jovyan/work/quakeflow_init.py << 'EOF'
import sys
import os
from pathlib import Path

# Add QuakeFlow to Python path
quakeflow_home = os.environ.get('QUAKEFLOW_HOME', '/opt/quakeflow')
if quakeflow_home not in sys.path:
    sys.path.insert(0, quakeflow_home)

# Set up default configuration
os.environ.setdefault('REGION_NAME', 'demo')
os.environ.setdefault('NUM_PARALLEL', '1')
os.environ.setdefault('ELYRA_RUNTIME_ENV', 'local')

print("QuakeFlow Enhanced Runtime initialized successfully!")
print(f"QuakeFlow Home: {quakeflow_home}")
print(f"Python Path: {sys.path[:3]}...")
print(f"Default Region: {os.environ.get('REGION_NAME')}")

# Test import of common utilities
try:
    from common import ElyraUtils, RegionConfig, EarthquakeAnalysisWorkflow
    print("✓ QuakeFlow common utilities imported successfully")
except ImportError as e:
    print(f"✗ Failed to import QuakeFlow utilities: {e}")

# Display available configurations
config_dir = Path(quakeflow_home) / 'configs'
if config_dir.exists():
    configs = list(config_dir.glob('*.json'))
    print(f"Available region configurations: {[c.stem for c in configs]}")
else:
    print("No region configurations found")
EOF

# Run initialization
cd /home/jovyan/work
python quakeflow_init.py

# Set up Jupyter configuration for enhanced environment
echo "Configuring Jupyter for QuakeFlow..."

# Create Jupyter configuration
mkdir -p /home/jovyan/.jupyter
cat > /home/jovyan/.jupyter/jupyter_lab_config.py << 'EOF'
# QuakeFlow Enhanced Jupyter Configuration

# Enable extensions
c.LabApp.collaborative = True
c.LabApp.terminado_settings = {'shell_command': ['/bin/bash']}

# Set up default working directory
import os
c.ServerApp.root_dir = '/home/jovyan/work'

# Enhanced logging
c.Application.log_level = 'INFO'

# Memory management
c.MappingKernelManager.cull_idle_timeout = 7200  # 2 hours
c.MappingKernelManager.cull_interval = 300       # 5 minutes

# Extension configuration for Elyra
c.ServerApp.jpserver_extensions = {
    'elyra': True,
    'jupyter_lsp': True,
}
EOF

# Create startup notebook
echo "Creating QuakeFlow startup notebook..."
cat > /home/jovyan/work/QuakeFlow_Startup.ipynb << 'EOF'
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# QuakeFlow Enhanced Runtime - Getting Started\n",
    "\n",
    "Welcome to the QuakeFlow Enhanced Runtime Environment! This notebook helps you get started with earthquake data processing using the unified framework."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Import QuakeFlow enhanced utilities\n",
    "from common import notebook_setup, ElyraUtils, RegionConfig\n",
    "import os\n",
    "\n",
    "print(\"QuakeFlow Enhanced Runtime Environment\")\n",
    "print(\"=\" * 40)\n",
    "print(f\"Runtime Environment: {os.environ.get('ELYRA_RUNTIME_ENV', 'local')}\")\n",
    "print(f\"Default Region: {os.environ.get('REGION_NAME', 'demo')}\")\n",
    "print(f\"Kubeflow Environment: {ElyraUtils.is_kubeflow_environment()}\")\n",
    "print(f\"Elyra Environment: {ElyraUtils.is_elyra_environment()}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# List available region configurations\n",
    "import glob\n",
    "from pathlib import Path\n",
    "\n",
    "config_dir = Path('/opt/quakeflow/configs')\n",
    "available_configs = list(config_dir.glob('*.json'))\n",
    "\n",
    "print(\"Available Region Configurations:\")\n",
    "for config_file in available_configs:\n",
    "    region_name = config_file.stem\n",
    "    try:\n",
    "        config = RegionConfig.from_json(str(config_file))\n",
    "        bounds = config.get_geographic_bounds()\n",
    "        print(f\"  - {region_name}: {bounds['minlatitude']:.1f}°-{bounds['maxlatitude']:.1f}°N, {bounds['minlongitude']:.1f}°-{bounds['maxlongitude']:.1f}°E\")\n",
    "    except Exception as e:\n",
    "        print(f\"  - {region_name}: (error loading config)\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Quick test of enhanced workflow\n",
    "print(\"Testing Enhanced Workflow Setup...\")\n",
    "\n",
    "# Set region for testing\n",
    "os.environ['REGION_NAME'] = 'california'\n",
    "\n",
    "try:\n",
    "    config, workflow, parallel_config = notebook_setup()\n",
    "    print(\"✓ Workflow setup successful\")\n",
    "    print(f\"  Region: {config.region}\")\n",
    "    print(f\"  Velocity Model: {config.get_velocity_model().model_type}\")\n",
    "    print(f\"  Parallel Config: {parallel_config}\")\n",
    "    \n",
    "    # Test processing configurations\n",
    "    phasenet_config = config.get_processing_config('phasenet')\n",
    "    gamma_config = config.get_processing_config('gamma')\n",
    "    \n",
    "    print(f\"  PhaseNet thresholds: P={phasenet_config.get('threshold_p', 0.3)}, S={phasenet_config.get('threshold_s', 0.3)}\")\n",
    "    print(f\"  GaMMA method: {gamma_config.get('method', 'BGMM')}\")\n",
    "    \n",
    "except Exception as e:\n",
    "    print(f\"✗ Workflow setup failed: {e}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Next Steps\n",
    "\n",
    "1. **Configure your region**: Set the `REGION_NAME` environment variable\n",
    "2. **Use enhanced notebooks**: Check the `templates/` directory for enhanced notebook templates\n",
    "3. **Build pipelines**: Use Elyra Pipeline Editor to create earthquake analysis workflows\n",
    "4. **Monitor progress**: Enhanced logging and Kubeflow UI metadata provide detailed progress tracking\n",
    "\n",
    "### Enhanced Templates Available:\n",
    "- `Set_Config_Enhanced.ipynb`: Unified configuration management\n",
    "- `Run_PhaseNet_Enhanced.ipynb`: Enhanced phase picking with quality control\n",
    "- `Run_GaMMA_Enhanced.ipynb`: Advanced event association with visualization\n",
    "\n",
    "Happy earthquake data processing! 🌍📊"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.9.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
EOF

# Create enhanced runtime configuration
echo "Creating enhanced runtime configuration..."
mkdir -p /home/jovyan/.local/share/jupyter/metadata/runtime-images

cat > /home/jovyan/.local/share/jupyter/metadata/runtime-images/quakeflow-enhanced.json << 'EOF'
{
    "name": "quakeflow-enhanced",
    "display_name": "QuakeFlow Enhanced Runtime",
    "metadata": {
        "tags": ["earthquake", "seismology", "enhanced", "unified"],
        "display_name": "QuakeFlow Enhanced Runtime",
        "image_name": "okadak86/quakeflow-enhanced:latest",
        "pull_policy": "IfNotPresent",
        "description": "Enhanced QuakeFlow runtime with unified common libraries and improved pipeline support"
    },
    "schema_name": "runtime-image"
}
EOF

# Set proper permissions
chown -R jovyan:users /home/jovyan/work
chown -R jovyan:users /home/jovyan/.jupyter
chown -R jovyan:users /home/jovyan/.local

echo "QuakeFlow Enhanced Runtime Environment setup complete!"
echo ""
echo "Available features:"
echo "  ✓ Unified common libraries"
echo "  ✓ Enhanced configuration management"
echo "  ✓ Improved error handling and logging"
echo "  ✓ Kubeflow UI metadata generation"
echo "  ✓ Quality control and validation"
echo "  ✓ Advanced visualization"
echo ""
echo "Starting Jupyter Lab..."

# Start Jupyter Lab
exec start-notebook.sh --NotebookApp.default_url=/lab
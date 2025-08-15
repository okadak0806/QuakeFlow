"""
Elyra Notebook utilities for QuakeFlow pipelines.

This module provides utilities specific to Elyra environment integration,
including Kubeflow Pipelines UI metadata generation and environment detection.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from .config import RegionConfig
from .workflow import EarthquakeAnalysisWorkflow


class ElyraUtils:
    """
    Utilities for Elyra notebook environment.
    """
    
    @staticmethod
    def is_elyra_environment() -> bool:
        """
        Check if running in Elyra environment.
        
        Returns:
            bool: True if running in Elyra environment
        """
        return os.environ.get('ELYRA_RUNTIME_ENV') is not None
    
    @staticmethod
    def is_kubeflow_environment() -> bool:
        """
        Check if running in Kubeflow Pipelines environment.
        
        Returns:
            bool: True if running in Kubeflow Pipelines
        """
        return os.environ.get('ELYRA_RUNTIME_ENV') == 'kfp'
    
    @staticmethod
    def get_region_from_env(default: str = 'california') -> str:
        """
        Get region name from environment variable.
        
        Args:
            default (str): Default region if not specified
            
        Returns:
            str: Region name
        """
        return os.environ.get('REGION_NAME', default)
    
    @staticmethod
    def setup_common_path():
        """
        Add common utilities to Python path for notebook imports.
        """
        # Get the directory containing this file
        current_dir = Path(__file__).parent
        examples_dir = current_dir.parent
        
        # Add to Python path if not already there
        if str(examples_dir) not in sys.path:
            sys.path.insert(0, str(examples_dir))
            
        print(f"Added {examples_dir} to Python path")
    
    @staticmethod
    def load_region_config(region: Optional[str] = None) -> RegionConfig:
        """
        Load region configuration from environment and config files.
        
        Args:
            region (str, optional): Region name. If None, gets from environment.
            
        Returns:
            RegionConfig: Loaded configuration
        """
        if region is None:
            region = ElyraUtils.get_region_from_env()
            
        # Try to load config file
        config_path = f"../../configs/{region}.json"
        if os.path.exists(config_path):
            return RegionConfig.from_json(config_path)
        else:
            print(f"Warning: Config file {config_path} not found, using defaults")
            return RegionConfig(region)
    
    @staticmethod
    def create_workflow(region: Optional[str] = None, 
                       config_path: Optional[str] = None) -> EarthquakeAnalysisWorkflow:
        """
        Create earthquake analysis workflow for Elyra environment.
        
        Args:
            region (str, optional): Region name
            config_path (str, optional): Path to config file
            
        Returns:
            EarthquakeAnalysisWorkflow: Configured workflow
        """
        if region is None:
            region = ElyraUtils.get_region_from_env()
            
        if config_path is None:
            config_path = f"../../configs/{region}.json"
            if not os.path.exists(config_path):
                config_path = None
                
        return EarthquakeAnalysisWorkflow(
            region=region,
            config_path=config_path,
            protocol="file",
            root_path="./"
        )
    
    @staticmethod
    def generate_kubeflow_metadata(
        title: str,
        markdown_content: str = None,
        metrics: Dict[str, Any] = None,
        outputs: List[Dict[str, Any]] = None
    ):
        """
        Generate Kubeflow Pipelines UI metadata.
        
        Args:
            title (str): Title for the metadata
            markdown_content (str, optional): Markdown content to display
            metrics (dict, optional): Metrics to display
            outputs (list, optional): Additional outputs
        """
        if not ElyraUtils.is_kubeflow_environment():
            print("Not in Kubeflow environment, skipping metadata generation")
            return
            
        metadata = {'outputs': []}
        
        # Add markdown content
        if markdown_content:
            metadata['outputs'].append({
                'storage': 'inline',
                'source': markdown_content,
                'type': 'markdown',
            })
        
        # Add metrics
        if metrics:
            for name, value in metrics.items():
                metadata['outputs'].append({
                    'name': name,
                    'numberValue': value,
                    'format': 'RAW',
                })
        
        # Add additional outputs
        if outputs:
            metadata['outputs'].extend(outputs)
            
        # Write metadata file
        with open('mlpipeline-ui-metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"Generated Kubeflow UI metadata: {title}")
    
    @staticmethod
    def log_pipeline_step(step_name: str, status: str = "completed", 
                         details: Dict[str, Any] = None):
        """
        Log pipeline step with standardized format.
        
        Args:
            step_name (str): Name of the pipeline step
            status (str): Status of the step
            details (dict, optional): Additional details
        """
        region = ElyraUtils.get_region_from_env()
        env_info = "KFP" if ElyraUtils.is_kubeflow_environment() else "Local"
        
        log_message = f"[{region.upper()}] [{env_info}] {step_name}: {status}"
        
        if details:
            for key, value in details.items():
                log_message += f"\n  - {key}: {value}"
                
        print(log_message)
    
    @staticmethod
    def save_pipeline_artifacts(artifacts: Dict[str, str], step_name: str):
        """
        Save pipeline artifacts with metadata.
        
        Args:
            artifacts (dict): Dictionary of artifact_name -> file_path
            step_name (str): Name of the pipeline step
        """
        region = ElyraUtils.get_region_from_env()
        
        # Create artifacts directory if it doesn't exist
        artifacts_dir = Path("artifacts")
        artifacts_dir.mkdir(exist_ok=True)
        
        # Create manifest
        manifest = {
            "step_name": step_name,
            "region": region,
            "artifacts": artifacts,
            "timestamp": str(Path().cwd())
        }
        
        manifest_path = artifacts_dir / f"{step_name}_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        ElyraUtils.log_pipeline_step(
            step_name, 
            "artifacts_saved", 
            {"count": len(artifacts), "manifest": str(manifest_path)}
        )
    
    @staticmethod
    def check_dependencies(required_files: List[str]) -> bool:
        """
        Check if required dependency files exist.
        
        Args:
            required_files (list): List of required file paths
            
        Returns:
            bool: True if all dependencies exist
        """
        missing_files = []
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                
        if missing_files:
            ElyraUtils.log_pipeline_step(
                "dependency_check", 
                "failed", 
                {"missing_files": missing_files}
            )
            return False
        else:
            ElyraUtils.log_pipeline_step(
                "dependency_check", 
                "passed", 
                {"checked_files": len(required_files)}
            )
            return True
    
    @staticmethod
    def get_parallel_config() -> Dict[str, int]:
        """
        Get parallel processing configuration from environment.
        
        Returns:
            dict: Parallel processing configuration
        """
        return {
            "num_parallel": int(os.environ.get('NUM_PARALLEL', 1)),
            "node_rank": int(os.environ.get('NODE_RANK', 0)),
            "world_size": int(os.environ.get('WORLD_SIZE', 1))
        }


def notebook_setup(region: Optional[str] = None) -> tuple:
    """
    Standard setup function for QuakeFlow notebooks.
    
    Args:
        region (str, optional): Region name
        
    Returns:
        tuple: (region_config, workflow, parallel_config)
    """
    # Setup Python path
    ElyraUtils.setup_common_path()
    
    # Load configuration
    if region is None:
        region = ElyraUtils.get_region_from_env()
        
    config = ElyraUtils.load_region_config(region)
    workflow = ElyraUtils.create_workflow(region)
    parallel_config = ElyraUtils.get_parallel_config()
    
    # Log setup info
    ElyraUtils.log_pipeline_step(
        "notebook_setup",
        "completed",
        {
            "region": region,
            "config_loaded": True,
            "parallel_workers": parallel_config["num_parallel"]
        }
    )
    
    return config, workflow, parallel_config


def notebook_finalize(step_name: str, results: Dict[str, Any] = None, 
                     artifacts: Dict[str, str] = None):
    """
    Standard finalization function for QuakeFlow notebooks.
    
    Args:
        step_name (str): Name of the processing step
        results (dict, optional): Processing results for metadata
        artifacts (dict, optional): Generated artifacts
    """
    # Save artifacts if provided
    if artifacts:
        ElyraUtils.save_pipeline_artifacts(artifacts, step_name)
    
    # Generate Kubeflow metadata
    if results:
        markdown_content = f"# {step_name} Results\n\n"
        metrics = {}
        
        for key, value in results.items():
            if isinstance(value, (int, float)):
                metrics[key] = value
                markdown_content += f"- **{key}**: {value}\n"
            else:
                markdown_content += f"- **{key}**: {value}\n"
                
        ElyraUtils.generate_kubeflow_metadata(
            title=f"{step_name} Complete",
            markdown_content=markdown_content,
            metrics=metrics if metrics else None
        )
    
    # Final log
    ElyraUtils.log_pipeline_step(step_name, "finalized")
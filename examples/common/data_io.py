"""
Data I/O utilities for QuakeFlow examples.
"""

import json
import pandas as pd
from pathlib import Path


class DataIO:
    """
    Data I/O handler supporting multiple file systems and formats.
    """
    
    def __init__(self, fs, protocol="file", root_path="./"):
        """
        Initialize data I/O handler.
        
        Args:
            fs: fsspec filesystem object
            protocol (str): File system protocol
            root_path (str): Root path for data
        """
        self.fs = fs
        self.protocol = protocol
        self.root_path = root_path
        
    def _get_full_path(self, file_path):
        """Get full path considering protocol."""
        if self.protocol == "file":
            return f"{self.root_path}/{file_path}"
        else:
            # For cloud storage, assume root_path is bucket name
            return f"{self.root_path}/{file_path}"
            
    def load_csv(self, file_path, **kwargs):
        """
        Load CSV file.
        
        Args:
            file_path (str): Path to CSV file
            **kwargs: Additional arguments for pd.read_csv
            
        Returns:
            pd.DataFrame: Loaded data
        """
        full_path = self._get_full_path(file_path)
        
        try:
            if self.protocol == "file":
                return pd.read_csv(full_path, **kwargs)
            else:
                with self.fs.open(full_path) as fp:
                    return pd.read_csv(fp, **kwargs)
        except Exception as e:
            raise IOError(f"Failed to load CSV from {full_path}: {e}")
            
    def load_json(self, file_path):
        """
        Load JSON file.
        
        Args:
            file_path (str): Path to JSON file
            
        Returns:
            dict or pd.DataFrame: Loaded data
        """
        full_path = self._get_full_path(file_path)
        
        try:
            if self.protocol == "file":
                with open(full_path, 'r') as f:
                    data = json.load(f)
            else:
                with self.fs.open(full_path, 'r') as fp:
                    data = json.load(fp)
                    
            # Convert to DataFrame if it's a list of dictionaries
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                return pd.DataFrame(data)
            elif isinstance(data, dict) and 'stations' in data:
                return pd.DataFrame(data['stations'])
            else:
                return data
                
        except Exception as e:
            raise IOError(f"Failed to load JSON from {full_path}: {e}")
            
    def load_parquet(self, file_path, **kwargs):
        """
        Load Parquet file.
        
        Args:
            file_path (str): Path to Parquet file
            **kwargs: Additional arguments for pd.read_parquet
            
        Returns:
            pd.DataFrame: Loaded data
        """
        full_path = self._get_full_path(file_path)
        
        try:
            if self.protocol == "file":
                return pd.read_parquet(full_path, **kwargs)
            else:
                with self.fs.open(full_path, 'rb') as fp:
                    return pd.read_parquet(fp, **kwargs)
        except Exception as e:
            raise IOError(f"Failed to load Parquet from {full_path}: {e}")
            
    def save_csv(self, data, file_path, **kwargs):
        """
        Save data as CSV.
        
        Args:
            data (pd.DataFrame): Data to save
            file_path (str): Output file path
            **kwargs: Additional arguments for to_csv
        """
        full_path = self._get_full_path(file_path)
        
        # Create directory if it doesn't exist
        if self.protocol == "file":
            Path(full_path).parent.mkdir(parents=True, exist_ok=True)
            data.to_csv(full_path, index=False, **kwargs)
        else:
            with self.fs.open(full_path, 'w') as fp:
                data.to_csv(fp, index=False, **kwargs)
                
    def save_json(self, data, file_path, **kwargs):
        """
        Save data as JSON.
        
        Args:
            data (dict or pd.DataFrame): Data to save
            file_path (str): Output file path
            **kwargs: Additional arguments for json.dump
        """
        full_path = self._get_full_path(file_path)
        
        # Convert DataFrame to dict if needed
        if isinstance(data, pd.DataFrame):
            data = data.to_dict('records')
            
        if self.protocol == "file":
            Path(full_path).parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                json.dump(data, f, indent=2, **kwargs)
        else:
            with self.fs.open(full_path, 'w') as fp:
                json.dump(data, fp, indent=2, **kwargs)
                
    def save_parquet(self, data, file_path, **kwargs):
        """
        Save data as Parquet.
        
        Args:
            data (pd.DataFrame): Data to save
            file_path (str): Output file path
            **kwargs: Additional arguments for to_parquet
        """
        full_path = self._get_full_path(file_path)
        
        if self.protocol == "file":
            Path(full_path).parent.mkdir(parents=True, exist_ok=True)
            data.to_parquet(full_path, index=False, **kwargs)
        else:
            with self.fs.open(full_path, 'wb') as fp:
                data.to_parquet(fp, index=False, **kwargs)
                
    def save_data(self, data, file_path, file_format="csv", **kwargs):
        """
        Save data in specified format.
        
        Args:
            data (pd.DataFrame): Data to save
            file_path (str): Output file path
            file_format (str): Output format ("csv", "json", "parquet")
            **kwargs: Additional arguments for save function
        """
        if file_format.lower() == "csv":
            self.save_csv(data, file_path, **kwargs)
        elif file_format.lower() == "json":
            self.save_json(data, file_path, **kwargs)
        elif file_format.lower() == "parquet":
            self.save_parquet(data, file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
            
    def exists(self, file_path):
        """
        Check if file exists.
        
        Args:
            file_path (str): Path to check
            
        Returns:
            bool: True if file exists
        """
        full_path = self._get_full_path(file_path)
        return self.fs.exists(full_path)
        
    def list_files(self, directory_path, pattern="*"):
        """
        List files in directory.
        
        Args:
            directory_path (str): Directory path
            pattern (str): File pattern to match
            
        Returns:
            list: List of file paths
        """
        full_path = self._get_full_path(directory_path)
        try:
            return self.fs.glob(f"{full_path}/{pattern}")
        except Exception as e:
            raise IOError(f"Failed to list files in {full_path}: {e}")
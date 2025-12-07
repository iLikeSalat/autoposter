"""
Configuration management for AutoPoster.
Handles loading and validation of configuration from YAML and environment variables.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for AutoPoster."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration.
        
        Args:
            config_path: Path to YAML configuration file
        """
        load_dotenv()
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                f"Please copy config.yaml.example to config.yaml and fill in your credentials"
            )
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _validate_config(self):
        """Validate required configuration."""
        # Check that at least one platform is enabled
        platforms = self.config.get('platforms', {})
        enable_threads = os.getenv('ENABLE_THREADS', '').lower() == 'true' or platforms.get('threads', False)
        enable_twitter = os.getenv('ENABLE_TWITTER', '').lower() == 'true' or platforms.get('twitter', False)
        
        if not enable_threads and not enable_twitter:
            raise ValueError(
                "At least one platform must be enabled. "
                "Set ENABLE_THREADS=true or ENABLE_TWITTER=true in .env"
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'llm.model')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_env_or_config(self, env_key: str, config_key: str, default: Any = None) -> Optional[str]:
        """Get value from environment variable or config file.
        
        Args:
            env_key: Environment variable key
            config_key: Configuration key (supports dot notation)
            default: Default value if neither found
            
        Returns:
            Value from env, config, or default
        """
        # Try environment variable first
        value = os.getenv(env_key)
        if value:
            return value
        
        # Try config file
        value = self.get(config_key)
        if value:
            return value
        
        return default


import os
import yaml
from typing import Dict, Any

def load_vertical(config_path: str = None) -> Dict[str, Any]:
    """Load vertical configuration from YAML file."""
    if not config_path:
        config_path = os.getenv("VERTICAL_CONFIG", "./configs/verticals/generic.yaml")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_env_or_raise(key: str) -> str:
    """Get environment variable or raise error if not found."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Environment variable {key} is required")
    return value
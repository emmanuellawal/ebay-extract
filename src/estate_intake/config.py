"""Configuration management for estate-intake."""

import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

DEFAULT_CONFIG = {
    "llm": {
        "enabled": False,
        "model": "gpt-4o-mini",
        "temperature": 0
    },
    "pricing": {
        "default_fee_pct": 0.13,
        "storage_cost_per_month": 50,
        "dom_cap_days": 90
    },
    "comps": {
        "provider": "stub",
        "window_days": 90
    },
    "io": {
        "image_max_edge_px": 3000,
        "ignore_prefix": "_"
    }
}

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result

def load_config(path: str = None) -> Dict[str, Any]:
    """
    Load configuration from defaults + optional YAML file.
    
    Args:
        path: Optional path to YAML config file
        
    Returns:
        Dict containing merged configuration
    """
    config = DEFAULT_CONFIG.copy()
    
    if path:
        config_path = Path(path)
        if config_path.exists():
            with open(config_path, 'r') as f:
                yaml_config = yaml.safe_load(f) or {}
            config = deep_merge(config, yaml_config)
    
    return config

def get_fee_pct(category_hint: str = None, config: Dict[str, Any] = None) -> float:
    """Get fee percentage for category (for now returns default)."""
    if config is None:
        config = DEFAULT_CONFIG
    
    return config["pricing"]["default_fee_pct"]

def get_storage_cost_per_month(cfg: Dict[str, Any]) -> float:
    """Get storage cost per month from config."""
    return cfg["pricing"]["storage_cost_per_month"]

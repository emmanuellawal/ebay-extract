"""Utility functions for estate-intake."""

import hashlib
from pathlib import Path
from typing import Any

def hash_content(content: Any) -> str:
    """Generate SHA-256 hash of content."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    elif not isinstance(content, bytes):
        content = str(content).encode('utf-8')
    
    return hashlib.sha256(content).hexdigest()

def ensure_directory(path: Path) -> Path:
    """Ensure directory exists and return path."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_filename(name: str) -> str:
    """Convert string to safe filename."""
    # Replace problematic characters
    safe_chars = []
    for char in name:
        if char.isalnum() or char in '-_. ':
            safe_chars.append(char)
        else:
            safe_chars.append('_')
    
    return ''.join(safe_chars).strip()

"""Discovery and fingerprinting for cases."""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.heic'}

def discover_cases(products_dir: Path, ignore_prefix: str = "_") -> List[Path]:
    """
    Return immediate subfolders not starting with ignore_prefix.
    
    Args:
        products_dir: Path to products directory
        ignore_prefix: Prefix to ignore (default "_")
        
    Returns:
        List of case directory paths
    """
    cases = []
    
    if not products_dir.exists() or not products_dir.is_dir():
        return cases
    
    for item in products_dir.iterdir():
        if item.is_dir() and not item.name.startswith(ignore_prefix):
            cases.append(item)
    
    return sorted(cases)

def collect_media(case_dir: Path, ignore_prefix: str = "_") -> List[Path]:
    """
    Include images with supported extensions, exclude names starting with ignore_prefix, sorted.
    
    Args:
        case_dir: Path to case directory
        ignore_prefix: Prefix to ignore (default "_")
        
    Returns:
        List of image file paths
    """
    media_files = []
    
    if not case_dir.exists() or not case_dir.is_dir():
        return media_files
    
    for file_path in case_dir.iterdir():
        if (file_path.is_file() and 
            file_path.suffix.lower() in SUPPORTED_EXTENSIONS and
            not file_path.name.startswith(ignore_prefix)):
            media_files.append(file_path)
    
    return sorted(media_files)

def read_hints(case_dir: Path) -> Dict[str, Any]:
    """
    Load product.json or case.json if present; else {}.
    
    Args:
        case_dir: Path to case directory
        
    Returns:
        Dict containing hints or empty dict
    """
    hints = {}
    
    # Try product.json first
    product_json = case_dir / "product.json"
    if product_json.exists():
        try:
            with open(product_json, 'r', encoding='utf-8') as f:
                hints = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Try case.json if no product.json
    if not hints:
        case_json = case_dir / "case.json"
        if case_json.exists():
            try:
                with open(case_json, 'r', encoding='utf-8') as f:
                    hints = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
    
    return hints

def compute_fingerprint(case_dir: Path, media_files: List[Path], hints: Dict[str, Any]) -> str:
    """
    SHA256 of filenames + sizes + mtimes + canonicalized hints JSON.
    
    Args:
        case_dir: Path to case directory
        media_files: List of media file paths
        hints: Dictionary of hints
        
    Returns:
        SHA256 hash string
    """
    hasher = hashlib.sha256()
    
    # Add case directory name
    hasher.update(case_dir.name.encode('utf-8'))
    
    # Add media file info
    for media_file in sorted(media_files):
        # Relative filename
        rel_name = media_file.relative_to(case_dir)
        hasher.update(str(rel_name).encode('utf-8'))
        
        # File size and mtime
        try:
            stat = media_file.stat()
            hasher.update(str(stat.st_size).encode('utf-8'))
            hasher.update(str(int(stat.st_mtime)).encode('utf-8'))
        except OSError:
            # File might not exist anymore
            hasher.update(b'missing')
    
    # Add canonicalized hints
    hints_json = json.dumps(hints, sort_keys=True, separators=(',', ':'))
    hasher.update(hints_json.encode('utf-8'))
    
    return hasher.hexdigest()

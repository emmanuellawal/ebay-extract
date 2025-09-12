"""Smoke tests for estate-intake pipeline."""

import json
import tempfile
from pathlib import Path
import pytest

from src.estate_intake.pipeline import process_all
from src.estate_intake.config import load_config


def test_pipeline_smoke():
    """Test that pipeline processes demo cases successfully."""
    # Load config
    config_path = Path("estate-intake-config.yaml")
    cfg = load_config(str(config_path) if config_path.exists() else None)
    
    # Process demo cases
    products_dir = Path("products")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        results_dir = Path(temp_dir)
        
        # Run pipeline
        manifest = process_all(products_dir, results_dir, cfg)
        
        # Basic assertions
        assert "cases" in manifest
        assert len(manifest["cases"]) >= 1
        
        # Check each case has required outputs
        for case in manifest["cases"]:
            case_id = case["case_id"]
            
            # Check item count
            assert case["item_count"] >= 1
            
            # Check output files exist
            case_dir = results_dir / case_id
            assert (case_dir / "_run_meta.json").exists()
            assert (case_dir / "estate_report.json").exists()
            assert (case_dir / "estate_report.html").exists()
            
            # Check estate report structure
            with open(case_dir / "estate_report.json") as f:
                estate_data = json.load(f)
            
            assert "totals" in estate_data
            assert "items" in estate_data
            assert len(estate_data["items"]) >= 1
            
            # Check each item has three quotes
            for item in estate_data["items"]:
                assert len(item["quotes"]) == 3
                strategies = {q["strategy"] for q in item["quotes"]}
                assert strategies == {"quick", "fair", "max"}


def test_determinism():
    """Test that running twice returns identical results."""
    config_path = Path("estate-intake-config.yaml")
    cfg = load_config(str(config_path) if config_path.exists() else None)
    
    products_dir = Path("products")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        results_dir = Path(temp_dir)
        
        # Run pipeline twice
        manifest1 = process_all(products_dir, results_dir, cfg)
        manifest2 = process_all(products_dir, results_dir, cfg)
        
        # Second run should have cache hits
        for case1, case2 in zip(manifest1["cases"], manifest2["cases"]):
            assert case1["case_id"] == case2["case_id"]
            assert case1["fingerprint"] == case2["fingerprint"]
            # First run: cache_hit = False, second run: cache_hit = True
            assert case2["cache_hit"] == True


if __name__ == "__main__":
    test_pipeline_smoke()
    test_determinism()
    print("All smoke tests passed!")

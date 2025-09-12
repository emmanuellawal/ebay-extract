"""Pipeline orchestration for estate-intake."""

import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, UTC
from PIL import Image

from .discovery import discover_cases, collect_media, read_hints, compute_fingerprint
from .llm_extract import extract_bundle
from .comps.ebay_stub import get_comp_stats
from .pricing import quotes_from_comps
from .reporting import build_item_report, build_estate_rollup, estate_html
from .config import get_fee_pct, get_storage_cost_per_month

logger = logging.getLogger(__name__)

def process_case(case_dir: Path, results_dir: Path, cfg: Dict[str, Any], force: bool = False, dry_run: bool = False) -> Dict[str, Any]:
    """
    Process a single case directory.
    
    Args:
        case_dir: Path to case directory
        results_dir: Path to results output directory
        cfg: Configuration dictionary
        force: If True, ignore cache and reprocess
        dry_run: If True, don't write files
        
    Returns:
        Dictionary with case processing summary
    """
    case_id = case_dir.name
    case_results_dir = results_dir / case_id
    
    logger.info(f"Processing case: {case_id}")
    
    started_at = datetime.now(UTC).isoformat()
    
    try:
        # Step 1: Discover
        media_files = collect_media(case_dir, cfg["io"]["ignore_prefix"])
        hints = read_hints(case_dir)
        fingerprint = compute_fingerprint(case_dir, media_files, hints)
        
        logger.info(f"Found {len(media_files)} media files")
        
        # Step 2: Cache Check
        run_meta_path = case_results_dir / "_run_meta.json"
        if not force and run_meta_path.exists():
            try:
                with open(run_meta_path, 'r') as f:
                    existing_meta = json.load(f)
                
                if existing_meta.get("fingerprint") == fingerprint:
                    logger.info("Cache hit - skipping processing")
                    return {
                        "case_id": case_id,
                        "cache_hit": True,
                        "item_count": existing_meta.get("item_count", 0),
                        "fingerprint": fingerprint
                    }
            except (json.JSONDecodeError, IOError):
                logger.warning("Failed to read existing run meta, will reprocess")
        
        # Step 3: Extract to IntakeBundle
        bundle = extract_bundle(case_id, media_files, hints, cfg)
        logger.info(f"Extracted {len(bundle.items)} items")
        
        # Assign SKUs if missing
        for i, item in enumerate(bundle.items):
            if not item.sku:
                short_hash = fingerprint[:8]
                item.sku = f"{case_id}-{i+1:03d}-{short_hash}"
        
        # Step 4: Process each item
        item_reports = []
        
        # Get comps for all items (async)
        async def get_all_comps():
            tasks = [get_comp_stats(item, cfg["comps"]["window_days"]) for item in bundle.items]
            return await asyncio.gather(*tasks)
        
        comp_stats_list = asyncio.run(get_all_comps())
        
        fee_pct = get_fee_pct(config=cfg)
        storage_cost = get_storage_cost_per_month(cfg)
        
        for item, comp_stats in zip(bundle.items, comp_stats_list):
            # Generate quotes
            quotes = quotes_from_comps(comp_stats, fee_pct, dom_cap_days=cfg["pricing"]["dom_cap_days"])
            
            # Build item report
            item_report = build_item_report(item, comp_stats, quotes, storage_cost)
            item_reports.append(item_report)
            
            if not dry_run:
                # Write item outputs
                item_dir = case_results_dir / "products" / item.sku
                item_dir.mkdir(parents=True, exist_ok=True)
                
                # metadata.json
                with open(item_dir / "metadata.json", 'w') as f:
                    json.dump(item.model_dump(), f, indent=2)
                
                # item_report.json
                with open(item_dir / "item_report.json", 'w') as f:
                    json.dump(item_report.model_dump(), f, indent=2)
                
                # Copy and normalize images
                images_dir = item_dir / "images"
                images_dir.mkdir(exist_ok=True)
                
                for i, media in enumerate(item.photos):
                    if media.source == "file" and media.path:
                        src_path = Path(media.path)
                        if src_path.exists():
                            # Copy and optionally resize
                            dst_path = images_dir / f"{i+1:02d}.jpg"
                            _copy_and_normalize_image(src_path, dst_path, cfg["io"]["image_max_edge_px"])
        
        # Step 5: Estate Roll-up
        rollup = build_estate_rollup(item_reports)
        estate_html_content = estate_html(item_reports, rollup)
        
        if not dry_run:
            case_results_dir.mkdir(parents=True, exist_ok=True)
            
            # estate_report.json
            with open(case_results_dir / "estate_report.json", 'w') as f:
                json.dump(rollup.model_dump(), f, indent=2)
            
            # estate_report.html
            with open(case_results_dir / "estate_report.html", 'w') as f:
                f.write(estate_html_content)
        
        # Step 6: Run Meta
        ended_at = datetime.now(UTC).isoformat()
        run_meta = {
            "case_id": case_id,
            "fingerprint": fingerprint,
            "started_at": started_at,
            "ended_at": ended_at,
            "item_count": len(bundle.items),
            "cache_hit": False,
            "warnings": [],
            "errors": []
        }
        
        if not dry_run:
            with open(run_meta_path, 'w') as f:
                json.dump(run_meta, f, indent=2)
        
        logger.info(f"Completed case: {case_id}")
        
        return {
            "case_id": case_id,
            "cache_hit": False,
            "item_count": len(bundle.items),
            "fingerprint": fingerprint,
            "output_paths": {
                "estate_report_json": str(case_results_dir / "estate_report.json"),
                "estate_report_html": str(case_results_dir / "estate_report.html"),
                "run_meta": str(run_meta_path)
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing case {case_id}: {e}")
        
        # Write error to run meta if not dry run
        if not dry_run:
            case_results_dir.mkdir(parents=True, exist_ok=True)
            error_meta = {
                "case_id": case_id,
                "started_at": started_at,
                "ended_at": datetime.now(UTC).isoformat(),
                "cache_hit": False,
                "item_count": 0,
                "errors": [str(e)]
            }
            with open(case_results_dir / "_run_meta.json", 'w') as f:
                json.dump(error_meta, f, indent=2)
        
        return {
            "case_id": case_id,
            "cache_hit": False,
            "item_count": 0,
            "error": str(e)
        }

def process_all(products_dir: Path, results_dir: Path, cfg: Dict[str, Any], force: bool = False, max_workers: int = 4, dry_run: bool = False) -> Dict[str, Any]:
    """
    Process all cases in products directory.
    
    Args:
        products_dir: Path to products directory
        results_dir: Path to results directory
        cfg: Configuration dictionary
        force: If True, ignore cache and reprocess
        max_workers: Maximum number of workers (unused in MVP)
        dry_run: If True, don't write files
        
    Returns:
        Manifest dictionary with case summaries
    """
    logger.info("Starting estate intake pipeline")
    
    # Discover cases
    cases = discover_cases(products_dir, cfg["io"]["ignore_prefix"])
    logger.info(f"Found {len(cases)} cases")
    
    case_summaries = []
    
    # Process cases sequentially (MVP)
    for case_dir in cases:
        summary = process_case(case_dir, results_dir, cfg, force, dry_run)
        case_summaries.append(summary)
    
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "products_dir": str(products_dir),
        "results_dir": str(results_dir),
        "total_cases": len(cases),
        "cases": case_summaries
    }
    
    logger.info("Estate intake pipeline completed")
    
    return manifest

def _copy_and_normalize_image(src_path: Path, dst_path: Path, max_edge_px: int):
    """Copy and optionally resize image."""
    try:
        with Image.open(src_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if needed
            width, height = img.size
            max_dim = max(width, height)
            
            if max_dim > max_edge_px:
                ratio = max_edge_px / max_dim
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save as JPEG
            img.save(dst_path, 'JPEG', quality=85)
            
    except Exception as e:
        logger.warning(f"Failed to process image {src_path}: {e}")
        # Fallback: just copy the file
        try:
            import shutil
            shutil.copy2(src_path, dst_path)
        except Exception as copy_error:
            logger.error(f"Failed to copy image {src_path}: {copy_error}")

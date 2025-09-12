"""CLI interface for estate-intake."""

import click
import logging
from pathlib import Path
from .config import load_config
from .pipeline import process_all

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Estate Intake MVP - Convert product photos to estate reports."""
    pass

@cli.command()
@click.option('--products', required=True, help='Products directory path')
@click.option('--results', required=True, help='Results output directory path')
@click.option('--force', is_flag=True, help='Ignore cache and reprocess')
@click.option('--dry-run', is_flag=True, help='Parse/compute but don\'t write results')
@click.option('--config', help='Custom config file path')
@click.option('--max-workers', default=4, help='Number of parallel workers')
@click.option('--log-level', default='INFO', help='Logging level')
def run(products, results, force, dry_run, config, max_workers, log_level):
    """Run the estate intake pipeline."""
    
    # Setup logging
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    logger.info("Starting estate intake pipeline")
    
    # Load configuration
    cfg = load_config(config)
    logger.info(f"Loaded configuration: {cfg}")
    
    # Convert paths
    products_dir = Path(products)
    results_dir = Path(results)
    
    if not products_dir.exists():
        logger.error(f"Products directory not found: {products_dir}")
        return
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    if dry_run:
        logger.info("DRY RUN MODE - No files will be written")
    
    try:
        # Process all cases
        manifest = process_all(
            products_dir=products_dir,
            results_dir=results_dir,
            cfg=cfg,
            force=force,
            max_workers=max_workers,
            dry_run=dry_run
        )
        
        # Write manifest
        if not dry_run:
            import json
            manifest_path = results_dir / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            logger.info(f"Manifest written to: {manifest_path}")
        
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == '__main__':
    cli()

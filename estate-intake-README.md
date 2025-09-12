# Estate-Intake MVP

An MVP pipeline that converts folders of product photos (plus optional hint JSON) into normalized product metadata, mock market comps, price/time recommendations, and estate-level reports.

## Purpose

Help estate sellers decide whether to sell fast (lower price) or wait (higher price) by estimating time-to-sell and net proceeds for each item, and totals for the estate.

## Quick Start

1. Set up environment:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux  
source .venv/bin/activate

pip install -r estate-intake-requirements.txt
```

2. Configure (optional):
```bash
cp .env.example .env
# Edit .env with your OpenAI API key if using LLM mode
```

3. Run the pipeline:
```bash
python -m src.estate_intake.cli run --products ./products --results ./results
```

## CLI Usage

```bash
estate-intake run --products ./products --results ./results [options]

Options:
  --force        Ignore cache and reprocess
  --dry-run      Parse/compute but don't write results
  --config FILE  Custom config file path
  --max-workers  Number of parallel workers (default: 4)
  --log-level    Logging level (default: INFO)
```

## Directory Structure

- **Input**: `products/` - Cases organized as folders with images and optional JSON hints
- **Output**: `results/` - Processed results with item reports, estate summaries, and HTML reports
- **Config**: `estate-intake-config.yaml` - Default configuration
- **Environment**: `.env` - API keys and environment settings

## Features

- **Offline Mode**: Works without API keys using deterministic fallbacks
- **Caching**: Idempotent runs with intelligent caching
- **Multiple Formats**: JSON metadata + HTML estate reports
- **Pricing Strategies**: Quick/Fair/Max pricing with time estimates
- **Estate Analysis**: Portfolio-level recommendations

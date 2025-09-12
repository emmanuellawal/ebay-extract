"""Deterministic eBay comps stub provider."""

import hashlib
import random
from ..models import Item, CompStats

async def get_comp_stats(item: Item, window_days: int = 90) -> CompStats:
    """
    Generate deterministic comp stats based on item sku+title.
    
    Args:
        item: Item to generate comps for
        window_days: Window days (currently unused in stub)
        
    Returns:
        CompStats with deterministic values
    """
    # Seed RNG with hash of sku+title
    seed_string = f"{item.sku}|{item.title}"
    seed_hash = hashlib.md5(seed_string.encode()).hexdigest()
    seed_value = int(seed_hash[:8], 16)
    
    rng = random.Random(seed_value)
    
    # Generate deterministic values
    median_sold = round(rng.uniform(30.0, 120.0), 2)
    p10_sold = round(0.7 * median_sold, 2)
    p90_sold = round(1.3 * median_sold, 2)
    avg_dom_days = rng.randint(7, 35)
    sold_count = rng.randint(10, 60)
    active_count = rng.randint(5, 40)
    
    sell_through_pct = round(sold_count / (sold_count + active_count), 3)
    
    return CompStats(
        sold_count=sold_count,
        active_count=active_count,
        sell_through_pct=sell_through_pct,
        median_sold=median_sold,
        p10_sold=p10_sold,
        p90_sold=p90_sold,
        avg_dom_days=float(avg_dom_days)
    )

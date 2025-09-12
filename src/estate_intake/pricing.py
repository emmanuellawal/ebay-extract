"""Pricing engine for estate-intake."""

from typing import List
from .models import CompStats, StrategyQuote

def quotes_from_comps(comp: CompStats, fee_pct: float, shipping_cost: float = None, dom_cap_days: int = 90) -> List[StrategyQuote]:
    """
    Convert CompStats to three StrategyQuote entries (quick, fair, max).
    
    Args:
        comp: CompStats from comps provider
        fee_pct: Fee percentage (e.g., 0.13 for 13%)
        shipping_cost: Estimated shipping cost (defaults to 0.0)
        dom_cap_days: Maximum days on market cap
        
    Returns:
        List of StrategyQuote objects for quick, fair, max
    """
    if shipping_cost is None:
        shipping_cost = 0.0
    
    # Calculate prices according to MVP rules
    quick_price = max(comp.p10_sold, 0.80 * comp.median_sold)
    fair_price = comp.median_sold
    max_price = min(comp.p90_sold, 1.20 * comp.median_sold)
    
    # Calculate DOM according to MVP rules
    quick_dom = max(3, int(0.5 * comp.avg_dom_days))
    fair_dom = int(comp.avg_dom_days)
    max_dom = min(dom_cap_days, int(1.75 * comp.avg_dom_days))
    
    quotes = []
    
    for strategy, price, dom in [
        ("quick", quick_price, quick_dom),
        ("fair", fair_price, fair_dom), 
        ("max", max_price, max_dom)
    ]:
        fees = price * fee_pct
        net = price - fees - shipping_cost
        
        quote = StrategyQuote(
            strategy=strategy,
            ask_price=round(price, 2),
            est_dom_days=dom,
            fee_pct=fee_pct,
            est_fees=round(fees, 2),
            est_shipping_cost=shipping_cost,
            est_net_proceeds=round(net, 2)
        )
        quotes.append(quote)
    
    return quotes

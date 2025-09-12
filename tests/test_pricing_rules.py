"""Test pricing rules and monotonicity."""

import pytest
from src.estate_intake.models import CompStats
from src.estate_intake.pricing import quotes_from_comps


def test_pricing_monotonicity():
    """Test that quick ≤ fair ≤ max for prices and DOM."""
    # Create sample comp stats
    comp = CompStats(
        sold_count=20,
        active_count=15,
        sell_through_pct=0.57,
        median_sold=100.0,
        p10_sold=70.0,
        p90_sold=130.0,
        avg_dom_days=20.0
    )
    
    # Get quotes
    quotes = quotes_from_comps(comp, fee_pct=0.13, dom_cap_days=90)
    
    # Extract by strategy
    quote_dict = {q.strategy: q for q in quotes}
    
    quick = quote_dict["quick"]
    fair = quote_dict["fair"]
    max_q = quote_dict["max"]
    
    # Test price monotonicity
    assert quick.ask_price <= fair.ask_price <= max_q.ask_price
    
    # Test DOM monotonicity
    assert quick.est_dom_days <= fair.est_dom_days <= max_q.est_dom_days
    
    # Test fee calculations
    for quote in quotes:
        expected_fees = quote.ask_price * 0.13
        assert abs(quote.est_fees - expected_fees) < 0.01
        
        # Test net calculation
        expected_net = quote.ask_price - quote.est_fees - quote.est_shipping_cost
        assert abs(quote.est_net_proceeds - expected_net) < 0.01


def test_pricing_rules_implementation():
    """Test specific pricing rule formulas."""
    comp = CompStats(
        sold_count=30,
        active_count=20,
        sell_through_pct=0.60,
        median_sold=80.0,
        p10_sold=56.0,  # 70% of median
        p90_sold=104.0,  # 130% of median
        avg_dom_days=14.0
    )
    
    quotes = quotes_from_comps(comp, fee_pct=0.15, shipping_cost=5.0, dom_cap_days=60)
    quote_dict = {q.strategy: q for q in quotes}
    
    # Test quick price: max(p10, 0.80 * median)
    expected_quick = max(comp.p10_sold, 0.80 * comp.median_sold)  # max(56, 64) = 64
    assert abs(quote_dict["quick"].ask_price - expected_quick) < 0.01
    
    # Test fair price: median
    assert abs(quote_dict["fair"].ask_price - comp.median_sold) < 0.01
    
    # Test max price: min(p90, 1.20 * median)
    expected_max = min(comp.p90_sold, 1.20 * comp.median_sold)  # min(104, 96) = 96
    assert abs(quote_dict["max"].ask_price - expected_max) < 0.01
    
    # Test DOM calculations
    quick_dom = max(3, int(0.5 * comp.avg_dom_days))  # max(3, 7) = 7
    fair_dom = int(comp.avg_dom_days)  # 14
    max_dom = min(60, int(1.75 * comp.avg_dom_days))  # min(60, 24) = 24
    
    assert quote_dict["quick"].est_dom_days == quick_dom
    assert quote_dict["fair"].est_dom_days == fair_dom
    assert quote_dict["max"].est_dom_days == max_dom


if __name__ == "__main__":
    test_pricing_monotonicity()
    test_pricing_rules_implementation()
    print("All pricing rule tests passed!")

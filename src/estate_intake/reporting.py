"""Reporting system for estate-intake."""

from typing import List, Dict, Any
from .models import Item, CompStats, StrategyQuote, ItemReport, EstateRollup

def build_item_report(item: Item, comp: CompStats, quotes: List[StrategyQuote], storage_cost_per_month: float) -> ItemReport:
    """
    Build ItemReport with recommendation heuristic.
    
    Args:
        item: Item being analyzed
        comp: CompStats from comps provider
        quotes: List of StrategyQuote objects (quick, fair, max)
        storage_cost_per_month: Monthly storage cost for recommendation logic
        
    Returns:
        ItemReport with recommendation
    """
    # Extract net proceeds for each strategy
    quote_dict = {q.strategy: q for q in quotes}
    
    quick_net = quote_dict["quick"].est_net_proceeds
    fair_net = quote_dict["fair"].est_net_proceeds
    max_net = quote_dict["max"].est_net_proceeds
    
    # Recommendation heuristic (MVP)
    notes = []
    
    if (max_net - fair_net) < storage_cost_per_month:
        recommendation = "fair"
        notes.append("Max premium doesn't justify storage cost")
    elif comp.sell_through_pct < 0.40:
        recommendation = "quick"
        notes.append(f"Low sell-through rate ({comp.sell_through_pct:.1%}) suggests quick sale")
    else:
        # Recommend strategy with highest net
        best_strategy = max(quote_dict.keys(), key=lambda s: quote_dict[s].est_net_proceeds)
        recommendation = best_strategy
        notes.append(f"Highest net proceeds strategy")
    
    notes_str = " • ".join(notes) if notes else None
    
    return ItemReport(
        sku=item.sku,
        title=item.title,
        category_hint=item.category_hint,
        condition_grade=item.condition_grade,
        comp=comp,
        quotes=quotes,
        recommendation=recommendation,
        notes=notes_str
    )

def build_estate_rollup(item_reports: List[ItemReport]) -> EstateRollup:
    """
    Build EstateRollup with totals for quick/fair/max.
    
    Args:
        item_reports: List of ItemReport objects
        
    Returns:
        EstateRollup with computed totals
    """
    if not item_reports:
        return EstateRollup(
            totals={
                "quick": {"gross": 0, "net": 0, "avg_dom": 0},
                "fair": {"gross": 0, "net": 0, "avg_dom": 0},
                "max": {"gross": 0, "net": 0, "avg_dom": 0}
            },
            items=[]
        )
    
    totals = {}
    
    for strategy in ["quick", "fair", "max"]:
        gross_total = 0
        net_total = 0
        dom_total = 0
        
        for report in item_reports:
            # Find quote for this strategy
            quote = next((q for q in report.quotes if q.strategy == strategy), None)
            if quote:
                gross_total += quote.ask_price
                net_total += quote.est_net_proceeds
                dom_total += quote.est_dom_days
        
        avg_dom = dom_total / len(item_reports) if item_reports else 0
        
        totals[strategy] = {
            "gross": round(gross_total, 2),
            "net": round(net_total, 2),
            "avg_dom": round(avg_dom, 1)
        }
    
    return EstateRollup(
        totals=totals,
        items=item_reports
    )

def estate_html(item_reports: List[ItemReport], rollup: EstateRollup) -> str:
    """
    Generate simple HTML estate report.
    
    Args:
        item_reports: List of ItemReport objects
        rollup: EstateRollup with totals
        
    Returns:
        HTML string for estate report
    """
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Estate Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .number { text-align: right; }
        .totals { background-color: #f9f9f9; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Estate Inventory Report</h1>
    <table>
        <thead>
            <tr>
                <th>SKU</th>
                <th>Title</th>
                <th>Condition</th>
                <th>Median Sold</th>
                <th>Sell-Through %</th>
                <th>Quick (Price / Net / Days)</th>
                <th>Fair (Price / Net / Days)</th>
                <th>Max (Price / Net / Days)</th>
                <th>Recommendation</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
"""
    
    # Add item rows
    for report in item_reports:
        quote_dict = {q.strategy: q for q in report.quotes}
        
        quick = quote_dict.get("quick")
        fair = quote_dict.get("fair")
        max_q = quote_dict.get("max")
        
        html += f"""
            <tr>
                <td>{report.sku}</td>
                <td>{report.title}</td>
                <td>{report.condition_grade}</td>
                <td class="number">${report.comp.median_sold:.2f}</td>
                <td class="number">{report.comp.sell_through_pct:.1%}</td>
                <td class="number">${quick.ask_price:.2f} / ${quick.est_net_proceeds:.2f} / {quick.est_dom_days}d</td>
                <td class="number">${fair.ask_price:.2f} / ${fair.est_net_proceeds:.2f} / {fair.est_dom_days}d</td>
                <td class="number">${max_q.ask_price:.2f} / ${max_q.est_net_proceeds:.2f} / {max_q.est_dom_days}d</td>
                <td><strong>{report.recommendation.upper()}</strong></td>
                <td>{report.notes or ''}</td>
            </tr>
        """
    
    # Add totals row
    totals = rollup.totals
    html += f"""
        </tbody>
        <tfoot>
            <tr class="totals">
                <td colspan="5">TOTALS</td>
                <td class="number">${totals['quick']['gross']:.2f} / ${totals['quick']['net']:.2f} / {totals['quick']['avg_dom']:.1f}d</td>
                <td class="number">${totals['fair']['gross']:.2f} / ${totals['fair']['net']:.2f} / {totals['fair']['avg_dom']:.1f}d</td>
                <td class="number">${totals['max']['gross']:.2f} / ${totals['max']['net']:.2f} / {totals['max']['avg_dom']:.1f}d</td>
                <td colspan="2"></td>
            </tr>
        </tfoot>
    </table>
</body>
</html>
"""
    
    return html

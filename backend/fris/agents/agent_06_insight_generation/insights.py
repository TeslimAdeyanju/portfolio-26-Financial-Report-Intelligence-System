"""Evidence-grounded management insights from validated movements and risks."""

from __future__ import annotations

from collections import defaultdict

from ...models import Evidence, FinancialInsight, FinancialMovement, RiskFinding


_MEANINGS = {
    "revenue": "This indicates the direction of the company's top-line scale.",
    "gross_profit": "This changes the resources available to cover operating costs and generate profit.",
    "operating_income": "This reflects the direction of profitability from core operations.",
    "net_income": "This affects retained earnings and returns attributable to shareholders.",
    "operating_cash_flow": "This indicates whether core operations are producing more or less cash.",
    "free_cash_flow": "This changes the cash available after capital investment for debt service, distributions, or reinvestment.",
    "ending_cash": "This changes the immediately available liquidity buffer.",
    "cash_and_equivalents": "This changes the immediately available liquidity buffer.",
    "total_debt": "This changes leverage, financing-cost exposure, and future repayment requirements.",
    "total_equity": "This changes the capital buffer available to absorb losses.",
    "current_ratio": "This changes the coverage of short-term liabilities by short-term assets.",
    "working_capital": "This changes the balance-sheet resources available for near-term operations.",
    "gross_margin": "This shows how much revenue remains after direct costs.",
    "operating_margin": "This shows how efficiently revenue is converted into core operating profit.",
    "net_margin": "This shows how efficiently revenue is converted into bottom-line profit.",
    "debt_to_equity": "This changes the balance between creditor and shareholder financing.",
    "debt_ratio": "This changes the proportion of the asset base financed by debt.",
    "asset_turnover": "This indicates whether the asset base is generating revenue more or less efficiently.",
    "return_on_assets": "This changes the return generated from the asset base.",
    "return_on_equity": "This changes the return generated on shareholder capital.",
}

_INVESTIGATIONS = {
    "revenue": "Investigate volume, pricing, mix, currency, acquisitions or disposals, and segment performance.",
    "gross_profit": "Reconcile the movement to revenue, product mix, input costs, and cost-of-sales changes.",
    "operating_income": "Review the gross-profit bridge, operating expenses, restructuring, and exceptional items.",
    "net_income": "Separate operating performance from interest, tax, non-operating, and exceptional effects.",
    "operating_cash_flow": "Review profit-to-cash conversion, receivables, inventory, payables, and non-cash items.",
    "free_cash_flow": "Reconcile operating cash flow and capital expenditure, including one-off investment programmes.",
    "ending_cash": "Review the cash-flow bridge, distributions, borrowing, acquisitions, and upcoming obligations.",
    "cash_and_equivalents": "Review the cash-flow bridge, distributions, borrowing, acquisitions, and upcoming obligations.",
    "total_debt": "Review new borrowing, repayments, maturities, interest rates, covenant headroom, and use of proceeds.",
    "total_equity": "Review retained earnings, dividends, buybacks, share issuance, and other comprehensive income.",
    "current_ratio": "Review receivable collection, inventory, payable timing, cash forecasts, and committed facilities.",
    "working_capital": "Review receivables, inventory, payables, seasonal requirements, and short-term funding.",
    "gross_margin": "Build a margin bridge across price, volume, mix, input costs, and currency.",
    "operating_margin": "Build a margin bridge across gross margin, payroll, overhead, restructuring, and exceptional items.",
    "net_margin": "Reconcile operating margin with financing costs, tax, and non-operating items.",
    "debt_to_equity": "Review debt movements alongside equity changes, covenant headroom, and refinancing capacity.",
    "debt_ratio": "Review borrowing composition, asset growth, maturity concentration, and repayment capacity.",
    "asset_turnover": "Review revenue growth against capital expenditure, acquisitions, disposals, and idle assets.",
    "return_on_assets": "Separate margin performance from asset utilisation and major changes in the asset base.",
    "return_on_equity": "Separate earnings performance from leverage, distributions, and changes in shareholder equity.",
}

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_STRATEGIC_ORDER = {
    "revenue": 0,
    "operating_income": 1,
    "net_income": 2,
    "operating_margin": 3,
    "operating_cash_flow": 4,
    "free_cash_flow": 5,
    "current_ratio": 6,
    "working_capital": 7,
    "total_debt": 8,
    "debt_to_equity": 9,
    "ending_cash": 10,
    "diluted_eps": 11,
    "basic_eps": 12,
}


def _period_key(period: str) -> tuple[int, str]:
    return (int(period), period) if period.isdigit() else (-1, period)


def _label(name: str) -> str:
    return name.replace("_", " ").title()


def _number(value: float) -> str:
    return f"({abs(value):,.2f})" if value < 0 else f"{value:,.2f}"


def _movement_narrative(movement: FinancialMovement) -> str:
    label = _label(movement.name)
    comparison = f"from {_number(movement.prior_value)} in {movement.prior_period} to {_number(movement.current_value)} in {movement.current_period}"
    if movement.direction in {"turnaround", "deterioration"}:
        return f"{label} recorded a {movement.direction}, moving {comparison}."
    if movement.unit == "percentage_points":
        return f"{label} {movement.direction} by {abs(movement.absolute_change):,.2f} percentage points, moving {comparison}."
    if movement.percentage_change is not None:
        return f"{label} {movement.direction} by {abs(movement.percentage_change):,.2f}%, moving {comparison}."
    return f"{label} {movement.direction}, moving {comparison}."


def _priority(movement: FinancialMovement, risks: list[RiskFinding]) -> str:
    if any(risk.severity == "high" for risk in risks):
        return "high"
    if risks or movement.direction in {"turnaround", "deterioration"}:
        return "medium"
    change = abs(movement.percentage_change or 0)
    if movement.assessment == "adverse" and change >= 10:
        return "medium"
    return "low"


def _score(insight: FinancialInsight, movement: FinancialMovement) -> tuple[int, int, int, float, str]:
    sentiment_rank = {"adverse": 0, "favorable": 1, "stable": 2, "contextual": 3}
    magnitude = abs(movement.percentage_change or movement.absolute_change)
    return (
        _PRIORITY_ORDER[insight.priority],
        _STRATEGIC_ORDER.get(movement.name, 50),
        sentiment_rank.get(insight.sentiment, 4),
        -magnitude,
        insight.code,
    )


def generate_financial_insights(
    movements: list[FinancialMovement],
    risks: list[RiskFinding],
    *,
    limit: int = 12,
) -> list[FinancialInsight]:
    """Generate ranked latest-period insights without asserting unverified causes."""
    if not movements or limit <= 0:
        return []
    latest = max((movement.current_period for movement in movements), key=_period_key)
    risk_by_metric: dict[str, list[RiskFinding]] = defaultdict(list)
    for risk in risks:
        if risk.period == latest:
            risk_by_metric[risk.metric].append(risk)

    ranked: list[tuple[tuple[int, int, float, str], FinancialInsight]] = []
    seen: set[str] = set()
    for movement in movements:
        if movement.current_period != latest or movement.assessment in {"stable", "contextual"}:
            continue
        # Prefer the calculated ratio over a duplicate fact for EPS; all other metrics are unique.
        if movement.name in seen:
            continue
        seen.add(movement.name)
        related_risks = risk_by_metric.get(movement.name, [])
        evidence: tuple[Evidence, ...] = (
            (movement.evidence,) if movement.evidence is not None else ()
        )
        risk_context = ""
        if related_risks:
            titles = ", ".join(risk.title.lower() for risk in related_risks)
            risk_context = f" The configured risk rules also flagged {titles}."
        insight = FinancialInsight(
            code=f"movement_{movement.name}_{latest}",
            title=f"{_label(movement.name)}: {movement.direction}",
            category=movement.category,
            priority=_priority(movement, related_risks),
            sentiment=movement.assessment,
            current_period=movement.current_period,
            prior_period=movement.prior_period,
            narrative=_movement_narrative(movement),
            business_meaning=(
                _MEANINGS.get(
                    movement.name,
                    "This movement may affect financial performance and should be assessed in business context.",
                )
                + risk_context
            ),
            investigation=_INVESTIGATIONS.get(
                movement.name,
                "Review the relevant report note and management commentary before attributing a cause.",
            ),
            related_metrics=(movement.name,),
            related_risks=tuple(risk.code for risk in related_risks),
            evidence=evidence,
        )
        ranked.append((_score(insight, movement), insight))

    return [insight for _, insight in sorted(ranked, key=lambda item: item[0])[:limit]]

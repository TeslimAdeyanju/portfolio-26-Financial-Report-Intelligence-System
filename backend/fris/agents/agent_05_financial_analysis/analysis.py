"""Deterministic trend and variance analysis over validated financial facts."""

from __future__ import annotations

from dataclasses import dataclass

from ...models import FinancialFact, FinancialMovement, Ratio


@dataclass(frozen=True)
class AnalysisPolicy:
    preference: str
    rationale: str


_FACT_POLICIES = {
    "revenue": AnalysisPolicy("higher", "revenue growth supports business expansion"),
    "cost_of_revenue": AnalysisPolicy("lower", "lower costs support profitability"),
    "gross_profit": AnalysisPolicy("higher", "higher gross profit strengthens operating capacity"),
    "operating_income": AnalysisPolicy("higher", "higher operating profit indicates stronger core performance"),
    "pretax_income": AnalysisPolicy("higher", "higher pretax income improves earnings capacity"),
    "net_income": AnalysisPolicy("higher", "higher net income improves shareholder returns"),
    "basic_eps": AnalysisPolicy("higher", "higher EPS improves earnings attributable per share"),
    "diluted_eps": AnalysisPolicy("higher", "higher diluted EPS improves earnings attributable per share"),
    "cash_and_equivalents": AnalysisPolicy("higher", "more cash generally strengthens liquidity headroom"),
    "current_assets": AnalysisPolicy("higher", "more current assets generally support short-term liquidity"),
    "current_liabilities": AnalysisPolicy("lower", "lower current obligations generally ease liquidity pressure"),
    "total_debt": AnalysisPolicy("lower", "lower debt generally reduces financing and solvency pressure"),
    "total_liabilities": AnalysisPolicy("lower", "lower liabilities generally reduce balance-sheet pressure"),
    "total_equity": AnalysisPolicy("higher", "higher equity strengthens the capital base"),
    "operating_cash_flow": AnalysisPolicy("higher", "higher operating cash flow strengthens cash generation"),
    "ending_cash": AnalysisPolicy("higher", "higher ending cash generally improves liquidity headroom"),
}

_RATIO_POLICIES = {
    "gross_margin": AnalysisPolicy("higher", "a higher gross margin indicates improved unit economics"),
    "operating_margin": AnalysisPolicy("higher", "a higher operating margin indicates improved core profitability"),
    "net_margin": AnalysisPolicy("higher", "a higher net margin indicates improved bottom-line profitability"),
    "current_ratio": AnalysisPolicy("higher", "a higher current ratio generally improves liquidity coverage"),
    "working_capital": AnalysisPolicy("higher", "higher working capital generally improves short-term resilience"),
    "debt_to_equity": AnalysisPolicy("lower", "lower debt-to-equity generally reduces financial leverage"),
    "debt_ratio": AnalysisPolicy("lower", "a lower debt ratio generally reduces balance-sheet leverage"),
    "asset_turnover": AnalysisPolicy("higher", "higher asset turnover indicates more efficient asset use"),
    "return_on_assets": AnalysisPolicy("higher", "higher ROA indicates improved returns on the asset base"),
    "return_on_equity": AnalysisPolicy("higher", "higher ROE indicates improved returns on shareholder capital"),
    "free_cash_flow": AnalysisPolicy("higher", "higher free cash flow increases financial flexibility"),
    "basic_eps": AnalysisPolicy("higher", "higher EPS improves earnings attributable per share"),
    "diluted_eps": AnalysisPolicy("higher", "higher diluted EPS improves earnings attributable per share"),
}


def _period_key(period: str) -> tuple[int, str]:
    return (int(period), period) if period.isdigit() else (-1, period)


def _change(current: float, prior: float) -> tuple[float, float | None, str]:
    absolute = round(current - prior, 2)
    if absolute == 0:
        return absolute, 0.0, "stable"
    relative = None
    if prior != 0 and (current == 0 or (current > 0) == (prior > 0)):
        relative = round((absolute / abs(prior)) * 100, 2)
    if relative is not None and abs(relative) < 1:
        return absolute, relative, "stable"
    if prior <= 0 < current:
        return absolute, None, "turnaround"
    if prior >= 0 > current:
        return absolute, None, "deterioration"
    return absolute, relative, "increased" if absolute > 0 else "decreased"


def _assessment(direction: str, policy: AnalysisPolicy | None) -> tuple[str, str]:
    if direction == "stable":
        return "stable", "the movement was below the 1% materiality threshold"
    if policy is None:
        return "contextual", "the movement requires business and industry context"
    if direction == "turnaround":
        assessment = "favorable" if policy.preference == "higher" else "adverse"
        return assessment, "the value moved from non-positive to positive"
    if direction == "deterioration":
        assessment = "adverse" if policy.preference == "higher" else "favorable"
        return assessment, "the value moved from non-negative to negative"
    favorable = (direction == "increased" and policy.preference == "higher") or (
        direction == "decreased" and policy.preference == "lower"
    )
    return ("favorable" if favorable else "adverse"), policy.rationale


def _movement(
    *,
    name: str,
    category: str,
    metric_type: str,
    current_period: str,
    prior_period: str,
    current: float,
    prior: float,
    policy: AnalysisPolicy | None,
    currency: str = "unknown",
    unit: str = "units",
    evidence=None,
) -> FinancialMovement:
    absolute, percentage, direction = _change(current, prior)
    assessment, rationale = _assessment(direction, policy)
    return FinancialMovement(
        name=name,
        category=category,
        metric_type=metric_type,
        current_period=current_period,
        prior_period=prior_period,
        current_value=current,
        prior_value=prior,
        absolute_change=absolute,
        percentage_change=percentage,
        direction=direction,
        assessment=assessment,
        rationale=rationale,
        currency=currency,
        unit=unit,
        evidence=evidence,
    )


def analyze_financial_performance(
    facts: dict[str, FinancialFact],
    period_ratios: dict[str, dict[str, Ratio]],
) -> list[FinancialMovement]:
    """Return every available adjacent-period fact and ratio movement."""
    movements: list[FinancialMovement] = []
    for name, fact in facts.items():
        if fact.status != "reported" or len(fact.values) < 2:
            continue
        periods = sorted(fact.values, key=_period_key, reverse=True)
        for current_period, prior_period in zip(periods, periods[1:]):
            movements.append(
                _movement(
                    name=name,
                    category=fact.category,
                    metric_type="fact",
                    current_period=current_period,
                    prior_period=prior_period,
                    current=fact.values[current_period],
                    prior=fact.values[prior_period],
                    policy=_FACT_POLICIES.get(name),
                    currency=fact.currency,
                    unit=fact.unit,
                    evidence=fact.evidence,
                )
            )

    ratio_periods = sorted(period_ratios, key=_period_key, reverse=True)
    for current_period, prior_period in zip(ratio_periods, ratio_periods[1:]):
        current_ratios = period_ratios[current_period]
        prior_ratios = period_ratios[prior_period]
        for name in current_ratios.keys() & prior_ratios.keys():
            if name in {"basic_eps", "diluted_eps"}:
                continue
            unit = (
                "percentage_points"
                if name.endswith("margin") or name.startswith("return_on_")
                else "amount"
                if name in {"working_capital", "free_cash_flow"}
                else "ratio"
            )
            movements.append(
                _movement(
                    name=name,
                    category="Calculated ratios",
                    metric_type="ratio",
                    current_period=current_period,
                    prior_period=prior_period,
                    current=current_ratios[name].value,
                    prior=prior_ratios[name].value,
                    policy=_RATIO_POLICIES.get(name),
                    unit=unit,
                )
            )
    return movements

"""Deterministic, evidence-linked financial risk assessment rules."""

from __future__ import annotations

from ...models import (
    FinancialFact,
    FinancialMovement,
    Ratio,
    RiskFinding,
    ValidationResult,
)


_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _period_key(period: str) -> tuple[int, str]:
    return (int(period), period) if period.isdigit() else (-1, period)


def _latest_period(
    facts: dict[str, FinancialFact], period_ratios: dict[str, dict[str, Ratio]]
) -> str | None:
    periods = set(period_ratios)
    for fact in facts.values():
        if fact.status == "reported":
            periods.update(fact.values)
    return max(periods, key=_period_key) if periods else None


def _fact_value(
    facts: dict[str, FinancialFact], name: str, period: str
) -> tuple[float, FinancialFact] | None:
    fact = facts.get(name)
    if not fact or fact.status != "reported" or period not in fact.values:
        return None
    return fact.values[period], fact


def _finding(
    code: str,
    title: str,
    category: str,
    severity: str,
    period: str,
    metric: str,
    observed: float,
    trigger: str,
    implication: str,
    action: str,
    *,
    unit: str = "units",
    evidence=None,
) -> RiskFinding:
    return RiskFinding(
        code=code,
        title=title,
        category=category,
        severity=severity,
        period=period,
        metric=metric,
        observed_value=round(observed, 2),
        trigger=trigger,
        implication=implication,
        suggested_action=action,
        unit=unit,
        evidence=evidence,
    )


def assess_financial_risks(
    facts: dict[str, FinancialFact],
    period_ratios: dict[str, dict[str, Ratio]],
    movements: list[FinancialMovement],
    validations: list[ValidationResult],
) -> list[RiskFinding]:
    """Identify material risks without treating unavailable facts as zero values."""
    findings: list[RiskFinding] = []
    latest = _latest_period(facts, period_ratios)

    for check in validations:
        if not check.passed:
            findings.append(
                _finding(
                    f"reporting_{check.name}",
                    "Financial statement reconciliation failed",
                    "Reporting quality",
                    "high",
                    check.period,
                    check.name,
                    abs(check.difference),
                    f"{check.formula}; difference must be within tolerance",
                    "The extracted figures do not reconcile, so related analysis may be unreliable.",
                    "Inspect the cited statement rows and correct extraction or source-data mapping before relying on the result.",
                    unit="difference",
                )
            )

    if latest is None:
        return findings

    ratios = period_ratios.get(latest, {})

    def add_fact_below(
        name: str, threshold: float, code: str, title: str, category: str,
        implication: str, action: str, severity: str = "high"
    ) -> None:
        item = _fact_value(facts, name, latest)
        if item and item[0] < threshold:
            value, fact = item
            findings.append(_finding(code, title, category, severity, latest, name, value,
                f"{name} < {threshold:g}", implication, action,
                unit=fact.unit, evidence=fact.evidence))

    add_fact_below(
        "operating_income", 0, "negative_operating_income", "Operating loss",
        "Profitability", "Core operations are not currently profitable.",
        "Review margin drivers, pricing, cost structure, and the path to operating break-even.",
    )
    add_fact_below(
        "net_income", 0, "negative_net_income", "Net loss", "Profitability",
        "Losses can weaken retained earnings and reduce financing flexibility.",
        "Identify recurring versus exceptional loss drivers and define a recovery plan.",
    )
    add_fact_below(
        "operating_cash_flow", 0, "negative_operating_cash_flow",
        "Negative operating cash flow", "Cash flow",
        "Operations are consuming cash rather than funding the business.",
        "Review working-capital movements and the cash conversion of reported earnings.",
    )
    add_fact_below(
        "total_equity", 0, "negative_equity", "Negative shareholders' equity",
        "Solvency", "Liabilities exceed assets attributable to shareholders.",
        "Review recapitalisation options, debt covenants, and going-concern assumptions.",
    )

    current_ratio = ratios.get("current_ratio")
    if current_ratio and current_ratio.value < 1:
        severity = "high" if current_ratio.value < 0.75 else "medium"
        findings.append(_finding(
            "weak_current_ratio", "Weak short-term liquidity coverage", "Liquidity",
            severity, latest, "current_ratio", current_ratio.value,
            "current ratio < 1.00x (high below 0.75x)",
            "Current assets may not fully cover current liabilities.",
            "Review cash forecasts, working-capital actions, and committed borrowing facilities.",
            unit="ratio",
        ))

    working_capital = ratios.get("working_capital")
    if working_capital and working_capital.value < 0:
        findings.append(_finding(
            "negative_working_capital", "Negative working capital", "Liquidity",
            "medium", latest, "working_capital", working_capital.value,
            "working capital < 0", "Short-term obligations exceed short-term assets.",
            "Examine payable timing, receivable collection, inventory, and refinancing capacity.",
            unit="amount",
        ))

    free_cash_flow = ratios.get("free_cash_flow")
    if free_cash_flow and free_cash_flow.value < 0:
        findings.append(_finding(
            "negative_free_cash_flow", "Negative free cash flow", "Cash flow",
            "high", latest, "free_cash_flow", free_cash_flow.value,
            "free cash flow < 0",
            "Internal cash generation may be insufficient after capital expenditure.",
            "Assess capital spending commitments, liquidity headroom, and external funding needs.",
            unit="amount",
        ))

    for name, medium, high, title in (
        ("debt_to_equity", 2, 3, "High debt relative to equity"),
        ("debt_ratio", 0.60, 0.75, "High balance-sheet leverage"),
    ):
        ratio = ratios.get(name)
        if ratio and ratio.value > medium:
            severity = "high" if ratio.value > high else "medium"
            findings.append(_finding(
                f"high_{name}", title, "Solvency", severity, latest, name,
                ratio.value, f"{name} > {medium:g}x (high above {high:g}x)",
                "Higher leverage increases refinancing, covenant, and interest-rate sensitivity.",
                "Review debt maturity, covenant headroom, interest coverage, and deleveraging options.",
                unit="ratio",
            ))

    latest_movements = [m for m in movements if m.current_period == latest]
    movement_by_name = {m.name: m for m in latest_movements}

    def add_decline(name: str, medium: float, high: float, code: str, title: str,
                    category: str, implication: str, action: str) -> None:
        movement = movement_by_name.get(name)
        change = movement.percentage_change if movement else None
        if movement and change is not None and change <= -medium:
            severity = "high" if change <= -high else "medium"
            findings.append(_finding(
                code, title, category, severity, latest, name, change,
                f"year-on-year change <= -{medium:g}% (high at -{high:g}%)",
                implication, action, unit="percentage", evidence=movement.evidence,
            ))

    add_decline("revenue", 5, 10, "material_revenue_decline", "Material revenue decline",
                "Performance", "A material decline may indicate weaker demand, pricing, or market position.",
                "Separate volume, price, currency, disposal, and segment drivers.")
    add_decline("free_cash_flow", 25, 50, "free_cash_flow_decline", "Material free cash flow decline",
                "Cash flow", "Reduced free cash flow lowers funding and distribution flexibility.",
                "Reconcile the decline to operating cash flow and capital expenditure drivers.")
    add_decline("ending_cash", 20, 40, "cash_balance_decline", "Material cash balance decline",
                "Liquidity", "A falling cash balance can reduce near-term liquidity headroom.",
                "Review the cash bridge, committed facilities, and the next 12 months of obligations.")

    debt_movement = movement_by_name.get("total_debt")
    if debt_movement and debt_movement.percentage_change is not None and debt_movement.percentage_change >= 20:
        severity = "high" if debt_movement.percentage_change >= 40 else "medium"
        findings.append(_finding(
            "material_debt_growth", "Material increase in debt", "Solvency", severity,
            latest, "total_debt", debt_movement.percentage_change,
            "year-on-year debt growth >= 20% (high at 40%)",
            "Rapid debt growth can increase financing costs and refinancing exposure.",
            "Determine how new borrowing was used and assess repayment capacity and covenant headroom.",
            unit="percentage", evidence=debt_movement.evidence,
        ))

    for name, title in (("operating_margin", "Operating margin compression"),
                        ("net_margin", "Net margin compression")):
        movement = movement_by_name.get(name)
        if movement and movement.absolute_change <= -3:
            severity = "high" if movement.absolute_change <= -5 else "medium"
            findings.append(_finding(
                f"{name}_compression", title, "Profitability", severity, latest, name,
                movement.absolute_change,
                "year-on-year margin decline >= 3 percentage points (high at 5 points)",
                "Margin compression indicates costs or other charges are growing faster than revenue.",
                "Reconcile the margin bridge across pricing, mix, input costs, and exceptional items.",
                unit="percentage_points",
            ))

    net_income = _fact_value(facts, "net_income", latest)
    operating_cash = _fact_value(facts, "operating_cash_flow", latest)
    if net_income and operating_cash and net_income[0] > 0 and operating_cash[0] < 0:
        findings.append(_finding(
            "earnings_cash_conversion", "Weak earnings-to-cash conversion", "Cash flow",
            "high", latest, "operating_cash_flow", operating_cash[0],
            "net income > 0 while operating cash flow < 0",
            "Reported profit is not converting into operating cash in the current period.",
            "Investigate receivables, inventory, payables, non-cash items, and revenue recognition.",
            unit=operating_cash[1].unit, evidence=operating_cash[1].evidence,
        ))

    unique = {(item.code, item.period): item for item in findings}
    return sorted(
        unique.values(),
        key=lambda item: (_SEVERITY_ORDER[item.severity], item.category, item.code),
    )

"""Deterministic financial calculations; no agent or LLM reasoning occurs here."""

from __future__ import annotations

from collections.abc import Callable

from ...models import FinancialStatement, Metric, Ratio


def _safe_divide(numerator: float, denominator: float) -> float | None:
    return None if denominator == 0 else numerator / denominator


def calculate_ratios(metrics: dict[str, Metric]) -> dict[str, Ratio]:
    values = {name: metric.value for name, metric in metrics.items()}
    specs: tuple[tuple[str, str, str, Callable[[float], float]], ...] = (
        ("gross_margin", "gross_profit", "revenue", lambda value: value * 100),
        ("operating_margin", "operating_profit", "revenue", lambda value: value * 100),
        ("net_margin", "net_income", "revenue", lambda value: value * 100),
        ("current_ratio", "current_assets", "current_liabilities", lambda value: value),
        ("return_on_assets", "net_income", "total_assets", lambda value: value * 100),
        ("return_on_equity", "net_income", "total_equity", lambda value: value * 100),
        ("debt_to_equity", "total_debt", "total_equity", lambda value: value),
    )

    results: dict[str, Ratio] = {}
    for name, numerator, denominator, transform in specs:
        if numerator not in values or denominator not in values:
            continue
        raw = _safe_divide(values[numerator], values[denominator])
        if raw is not None:
            results[name] = Ratio(
                name=name,
                value=round(transform(raw), 2),
                formula=f"{numerator} / {denominator}",
            )
    return results


def _statement_value(
    statements: dict[str, FinancialStatement],
    statement: str,
    row: str,
    period: str,
) -> float | None:
    item = statements.get(statement)
    if not item or row not in item.rows:
        return None
    return item.rows[row].values.get(period)


def _add_ratio(
    target: dict[str, Ratio],
    name: str,
    numerator: float | None,
    denominator: float | None,
    formula: str,
    *,
    percentage: bool = False,
) -> None:
    if numerator is None or denominator in (None, 0):
        return
    value = numerator / denominator
    target[name] = Ratio(name, round(value * 100 if percentage else value, 2), formula)


def calculate_period_ratios(
    statements: dict[str, FinancialStatement],
) -> dict[str, dict[str, Ratio]]:
    """Calculate KPIs for every period using average balances where available."""
    income = statements.get("income_statement")
    balance = statements.get("balance_sheet")
    cash_flow = statements.get("cash_flow_statement")
    periods = income.periods if income else (balance.periods if balance else ())
    results: dict[str, dict[str, Ratio]] = {}

    for period in periods:
        period_results: dict[str, Ratio] = {}
        revenue = _statement_value(statements, "income_statement", "revenue", period)
        gross_profit = _statement_value(statements, "income_statement", "gross_profit", period)
        operating_income = _statement_value(statements, "income_statement", "operating_income", period)
        net_income = _statement_value(statements, "income_statement", "net_income", period)
        current_assets = _statement_value(statements, "balance_sheet", "current_assets", period)
        current_liabilities = _statement_value(statements, "balance_sheet", "current_liabilities", period)
        total_assets = _statement_value(statements, "balance_sheet", "total_assets", period)
        total_equity = _statement_value(statements, "balance_sheet", "total_equity", period)
        total_debt = _statement_value(statements, "balance_sheet", "total_debt", period)

        _add_ratio(period_results, "gross_margin", gross_profit, revenue, "gross_profit / revenue", percentage=True)
        _add_ratio(period_results, "operating_margin", operating_income, revenue, "operating_income / revenue", percentage=True)
        _add_ratio(period_results, "net_margin", net_income, revenue, "net_income / revenue", percentage=True)
        _add_ratio(period_results, "current_ratio", current_assets, current_liabilities, "current_assets / current_liabilities")
        _add_ratio(period_results, "debt_to_equity", total_debt, total_equity, "total_debt / total_equity")
        _add_ratio(period_results, "debt_ratio", total_debt, total_assets, "total_debt / total_assets")

        if current_assets is not None and current_liabilities is not None:
            period_results["working_capital"] = Ratio(
                "working_capital",
                round(current_assets - current_liabilities, 2),
                "current_assets - current_liabilities",
            )

        if balance and period in balance.periods:
            prior_period = str(int(period) - 1) if period.isdigit() else ""
            if prior_period in balance.periods:
                prior_assets = _statement_value(statements, "balance_sheet", "total_assets", prior_period)
                prior_equity = _statement_value(statements, "balance_sheet", "total_equity", prior_period)
                average_assets = (
                    (total_assets + prior_assets) / 2
                    if total_assets is not None and prior_assets is not None
                    else None
                )
                average_equity = (
                    (total_equity + prior_equity) / 2
                    if total_equity is not None and prior_equity is not None
                    else None
                )
                _add_ratio(period_results, "asset_turnover", revenue, average_assets, "revenue / average_total_assets")
                _add_ratio(period_results, "return_on_assets", net_income, average_assets, "net_income / average_total_assets", percentage=True)
                _add_ratio(period_results, "return_on_equity", net_income, average_equity, "net_income / average_total_equity", percentage=True)

        operating_cash = _statement_value(statements, "cash_flow_statement", "operating_cash_flow", period)
        capex = _statement_value(statements, "cash_flow_statement", "capital_expenditure", period)
        if operating_cash is not None and capex is not None:
            period_results["free_cash_flow"] = Ratio(
                "free_cash_flow",
                round(operating_cash + capex, 2),
                "operating_cash_flow + capital_expenditure",
            )

        for eps_name in ("basic_eps", "diluted_eps"):
            eps = _statement_value(statements, "income_statement", eps_name, period)
            if eps is not None:
                period_results[eps_name] = Ratio(eps_name, eps, "reported value")

        results[period] = period_results
    return results

"""Data Quality Agent: deterministic financial statement reconciliations."""

from __future__ import annotations

from ...models import FinancialStatement, Ratio, ValidationResult


def _value(statement: FinancialStatement | None, row: str, period: str) -> float | None:
    if not statement or row not in statement.rows:
        return None
    return statement.rows[row].values.get(period)


def _validation(
    name: str,
    period: str,
    formula: str,
    actual: float,
    expected: float,
    tolerance: float = 1.0,
) -> ValidationResult:
    difference = round(actual - expected, 2)
    return ValidationResult(
        name=name,
        period=period,
        passed=abs(difference) <= tolerance,
        formula=formula,
        actual=actual,
        expected=expected,
        difference=difference,
    )


def validate_financials(
    statements: dict[str, FinancialStatement],
    period_ratios: dict[str, dict[str, Ratio]],
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    income = statements.get("income_statement")
    balance = statements.get("balance_sheet")

    if balance:
        for period in balance.periods:
            assets = _value(balance, "total_assets", period)
            liabilities = _value(balance, "total_liabilities", period)
            equity = _value(balance, "total_equity", period)
            if None not in (assets, liabilities, equity):
                results.append(
                    _validation(
                        "accounting_equation",
                        period,
                        "total_assets = total_liabilities + total_equity",
                        assets,
                        liabilities + equity,
                    )
                )

            current_assets = _value(balance, "current_assets", period)
            current_liabilities = _value(balance, "current_liabilities", period)
            ratio = period_ratios.get(period, {}).get("current_ratio")
            if current_assets is not None and current_liabilities not in (None, 0) and ratio:
                results.append(
                    _validation(
                        "current_ratio",
                        period,
                        "current_ratio = current_assets / current_liabilities",
                        ratio.value,
                        round(current_assets / current_liabilities, 2),
                        tolerance=0.01,
                    )
                )

    if income:
        for period in income.periods:
            revenue = _value(income, "revenue", period)
            cost = _value(income, "cost_of_revenue", period)
            gross_profit = _value(income, "gross_profit", period)
            if None not in (revenue, cost, gross_profit):
                results.append(
                    _validation(
                        "gross_profit_reconciliation",
                        period,
                        "gross_profit = revenue - cost_of_revenue",
                        gross_profit,
                        revenue - cost,
                    )
                )
    return results

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
    cash_flow = statements.get("cash_flow_statement")

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

            combined_total = _value(balance, "total_liabilities_and_equity", period)
            if assets is not None and combined_total is not None:
                results.append(
                    _validation(
                        "balance_sheet_total",
                        period,
                        "total_assets = total_liabilities_and_equity",
                        assets,
                        combined_total,
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
    if cash_flow:
        for period in cash_flow.periods:
            beginning = _value(cash_flow, "beginning_cash", period)
            ending = _value(cash_flow, "ending_cash", period)
            change = _value(cash_flow, "net_change_in_cash", period)
            if None not in (beginning, ending, change):
                results.append(
                    _validation(
                        "cash_rollforward",
                        period,
                        "ending_cash = beginning_cash + net_change_in_cash",
                        ending,
                        beginning + change,
                    )
                )

            operating = _value(cash_flow, "operating_cash_flow", period)
            investing = _value(cash_flow, "investing_cash_flow", period)
            financing = _value(cash_flow, "financing_cash_flow", period)
            foreign_exchange = _value(cash_flow, "foreign_exchange_effect", period)
            if None not in (change, operating, investing, financing, foreign_exchange):
                results.append(
                    _validation(
                        "cash_flow_reconciliation",
                        period,
                        "net_change_in_cash = operating + investing + financing + foreign_exchange",
                        change,
                        operating + investing + financing + foreign_exchange,
                    )
                )
    return results

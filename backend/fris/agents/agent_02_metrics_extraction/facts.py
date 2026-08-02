"""Canonical, evidence-backed financial facts for cross-company analysis."""

from __future__ import annotations

from dataclasses import dataclass

from ...models import FinancialFact, FinancialStatement


@dataclass(frozen=True)
class FactDefinition:
    name: str
    category: str
    statement: str
    rows: tuple[str, ...]
    optional: bool = False


FACT_DEFINITIONS = (
    FactDefinition("revenue", "Income statement", "income_statement", ("revenue",)),
    FactDefinition(
        "cost_of_revenue",
        "Income statement",
        "income_statement",
        ("cost_of_revenue",),
        optional=True,
    ),
    FactDefinition(
        "gross_profit",
        "Income statement",
        "income_statement",
        ("gross_profit",),
        optional=True,
    ),
    FactDefinition(
        "operating_income",
        "Income statement",
        "income_statement",
        ("operating_income",),
    ),
    FactDefinition(
        "pretax_income",
        "Income statement",
        "income_statement",
        ("pretax_income",),
    ),
    FactDefinition(
        "income_tax_expense",
        "Income statement",
        "income_statement",
        ("income_tax_expense",),
    ),
    FactDefinition("net_income", "Income statement", "income_statement", ("net_income",)),
    FactDefinition(
        "basic_eps", "Per share", "income_statement", ("basic_eps",), optional=True
    ),
    FactDefinition(
        "diluted_eps", "Per share", "income_statement", ("diluted_eps",), optional=True
    ),
    FactDefinition(
        "cash_and_equivalents",
        "Balance sheet",
        "balance_sheet",
        ("cash_and_equivalents",),
    ),
    FactDefinition(
        "current_assets",
        "Balance sheet",
        "balance_sheet",
        ("current_assets",),
        optional=True,
    ),
    FactDefinition("total_assets", "Balance sheet", "balance_sheet", ("total_assets",)),
    FactDefinition(
        "current_liabilities",
        "Balance sheet",
        "balance_sheet",
        ("current_liabilities",),
        optional=True,
    ),
    FactDefinition(
        "total_debt",
        "Balance sheet",
        "balance_sheet",
        ("total_debt", "term_debt"),
        optional=True,
    ),
    FactDefinition(
        "total_liabilities",
        "Balance sheet",
        "balance_sheet",
        ("total_liabilities",),
    ),
    FactDefinition("total_equity", "Balance sheet", "balance_sheet", ("total_equity",)),
    FactDefinition(
        "operating_cash_flow",
        "Cash flow",
        "cash_flow_statement",
        ("operating_cash_flow",),
    ),
    FactDefinition(
        "capital_expenditure",
        "Cash flow",
        "cash_flow_statement",
        ("capital_expenditure",),
        optional=True,
    ),
    FactDefinition(
        "investing_cash_flow",
        "Cash flow",
        "cash_flow_statement",
        ("investing_cash_flow",),
    ),
    FactDefinition(
        "financing_cash_flow",
        "Cash flow",
        "cash_flow_statement",
        ("financing_cash_flow",),
    ),
    FactDefinition(
        "ending_cash", "Cash flow", "cash_flow_statement", ("ending_cash",)
    ),
)


def extract_financial_facts(
    statements: dict[str, FinancialStatement],
) -> dict[str, FinancialFact]:
    """Map differing report labels into a stable analysis-oriented fact pack."""
    facts: dict[str, FinancialFact] = {}
    for definition in FACT_DEFINITIONS:
        statement = statements.get(definition.statement)
        row = None
        if statement is not None:
            row = next(
                (statement.rows[name] for name in definition.rows if name in statement.rows),
                None,
            )
        if statement is None:
            reason = f"The {definition.statement.replace('_', ' ')} was not identified."
        elif row is None:
            qualifier = "Optional metric; " if definition.optional else ""
            reason = f"{qualifier}not found as a separately reported line item."
        else:
            facts[definition.name] = FinancialFact(
                name=definition.name,
                category=definition.category,
                values=row.values,
                source_label=row.label or row.name,
                currency=statement.currency,
                unit=statement.unit,
                unit_scale=statement.unit_scale,
                evidence=row.evidence,
                extraction_method=row.extraction_method,
                confidence=row.confidence,
            )
            continue

        facts[definition.name] = FinancialFact(
            name=definition.name,
            category=definition.category,
            values={},
            status="not_found",
            reason=reason,
            confidence=0.0,
        )
    return facts

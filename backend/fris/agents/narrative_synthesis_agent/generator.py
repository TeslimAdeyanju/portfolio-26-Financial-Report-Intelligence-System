"""Narrative Synthesis Agent: transparent baseline report commentary."""

from __future__ import annotations

from ...models import Metric, Ratio


def generate_summary(metrics: dict[str, Metric], ratios: dict[str, Ratio]) -> list[str]:
    statements: list[str] = []
    if revenue := metrics.get("revenue"):
        statements.append(f"Reported revenue was {revenue.value:,.2f}.")
    for key, label in (
        ("gross_margin", "Gross margin"),
        ("operating_margin", "Operating margin"),
        ("net_margin", "Net margin"),
        ("return_on_assets", "Return on assets"),
        ("return_on_equity", "Return on equity"),
    ):
        if ratio := ratios.get(key):
            statements.append(f"{label} was {ratio.value:.2f}%.")
    for key, label in (("current_ratio", "Current ratio"), ("debt_to_equity", "Debt-to-equity")):
        if ratio := ratios.get(key):
            statements.append(f"{label} was {ratio.value:.2f}x.")
    if not statements:
        statements.append("No supported financial metrics were confidently extracted.")
    return statements

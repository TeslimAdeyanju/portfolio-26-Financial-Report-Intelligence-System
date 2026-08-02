from fris.agents.financial_calculation_engine import calculate_ratios
from fris.models import Metric


def test_calculates_supported_ratios() -> None:
    metrics = {
        "revenue": Metric("revenue", 1_000),
        "gross_profit": Metric("gross_profit", 400),
        "net_income": Metric("net_income", 100),
        "current_assets": Metric("current_assets", 300),
        "current_liabilities": Metric("current_liabilities", 150),
    }

    ratios = calculate_ratios(metrics)

    assert ratios["gross_margin"].value == 40.0
    assert ratios["net_margin"].value == 10.0
    assert ratios["current_ratio"].value == 2.0


def test_skips_ratios_with_missing_or_zero_denominator() -> None:
    metrics = {
        "net_income": Metric("net_income", 100),
        "revenue": Metric("revenue", 0),
    }

    assert "net_margin" not in calculate_ratios(metrics)

from fris.agents.agent_07_risk_assessment import assess_financial_risks
from fris.models import FinancialFact, FinancialMovement, Ratio, ValidationResult


def _fact(name: str, values: dict[str, float]) -> FinancialFact:
    return FinancialFact(name=name, category="Test", values=values, unit="millions")


def _movement(name: str, change: float, absolute: float = 0) -> FinancialMovement:
    return FinancialMovement(
        name=name,
        category="Test",
        metric_type="fact",
        current_period="2025",
        prior_period="2024",
        current_value=80,
        prior_value=100,
        absolute_change=absolute,
        percentage_change=change,
        direction="decreased",
        assessment="adverse",
        rationale="test",
    )


def test_detects_profitability_liquidity_and_cash_flow_risks() -> None:
    risks = assess_financial_risks(
        {
            "operating_income": _fact("operating_income", {"2025": -10}),
            "net_income": _fact("net_income", {"2025": 5}),
            "operating_cash_flow": _fact("operating_cash_flow", {"2025": -3}),
        },
        {"2025": {
            "current_ratio": Ratio("current_ratio", 0.7, "x"),
            "working_capital": Ratio("working_capital", -20, "x"),
            "free_cash_flow": Ratio("free_cash_flow", -8, "x"),
        }},
        [],
        [],
    )
    by_code = {risk.code: risk for risk in risks}

    assert by_code["negative_operating_income"].severity == "high"
    assert by_code["weak_current_ratio"].severity == "high"
    assert by_code["negative_working_capital"].severity == "medium"
    assert by_code["negative_free_cash_flow"].severity == "high"
    assert by_code["earnings_cash_conversion"].severity == "high"


def test_detects_material_movement_and_leverage_thresholds() -> None:
    risks = assess_financial_risks(
        {},
        {"2025": {
            "debt_to_equity": Ratio("debt_to_equity", 3.5, "x"),
            "debt_ratio": Ratio("debt_ratio", 0.65, "x"),
        }},
        [
            _movement("revenue", -12),
            _movement("total_debt", 45),
            _movement("operating_margin", -20, absolute=-4),
        ],
        [],
    )
    by_code = {risk.code: risk for risk in risks}

    assert by_code["material_revenue_decline"].severity == "high"
    assert by_code["material_debt_growth"].severity == "high"
    assert by_code["high_debt_to_equity"].severity == "high"
    assert by_code["high_debt_ratio"].severity == "medium"
    assert by_code["operating_margin_compression"].severity == "medium"


def test_failed_reconciliation_becomes_reporting_risk() -> None:
    risks = assess_financial_risks(
        {}, {}, [],
        [ValidationResult("accounting_equation", "2025", False, "A = L + E", 90, 100, -10)],
    )

    assert len(risks) == 1
    assert risks[0].code == "reporting_accounting_equation"
    assert risks[0].severity == "high"
    assert risks[0].observed_value == 10


def test_missing_or_healthy_metrics_do_not_create_false_risks() -> None:
    risks = assess_financial_risks(
        {
            "net_income": _fact("net_income", {"2025": 10}),
            "missing": FinancialFact("missing", "Test", {}, status="not_found"),
        },
        {"2025": {"current_ratio": Ratio("current_ratio", 1.5, "x")}},
        [],
        [ValidationResult("accounting_equation", "2025", True, "A = L + E", 100, 100, 0)],
    )

    assert risks == []

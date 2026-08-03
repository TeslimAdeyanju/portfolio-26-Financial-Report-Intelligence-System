from fris.agents.agent_05_financial_analysis import analyze_financial_performance
from fris.models import FinancialFact, Ratio


def _fact(name: str, values: dict[str, float], category: str = "Test") -> FinancialFact:
    return FinancialFact(name=name, category=category, values=values)


def test_classifies_growth_leverage_and_profit_turnaround() -> None:
    movements = analyze_financial_performance(
        {
            "revenue": _fact("revenue", {"2025": 100, "2024": 90}),
            "total_debt": _fact("total_debt", {"2025": 60, "2024": 50}),
            "net_income": _fact("net_income", {"2025": 10, "2024": -5}),
        },
        {},
    )
    by_name = {movement.name: movement for movement in movements}

    assert by_name["revenue"].absolute_change == 10
    assert by_name["revenue"].percentage_change == 11.11
    assert by_name["revenue"].assessment == "favorable"
    assert by_name["total_debt"].assessment == "adverse"
    assert by_name["net_income"].direction == "turnaround"
    assert by_name["net_income"].percentage_change is None
    assert by_name["net_income"].assessment == "favorable"


def test_marks_immaterial_and_context_dependent_movements() -> None:
    movements = analyze_financial_performance(
        {
            "revenue": _fact("revenue", {"2025": 100.5, "2024": 100}),
            "capital_expenditure": _fact(
                "capital_expenditure", {"2025": -20, "2024": -10}
            ),
            "financing_cash_flow": _fact(
                "financing_cash_flow", {"2025": 20, "2024": -10}
            ),
            "missing": FinancialFact(
                name="missing",
                category="Test",
                values={},
                status="not_found",
            ),
        },
        {},
    )
    by_name = {movement.name: movement for movement in movements}

    assert by_name["revenue"].direction == "stable"
    assert by_name["revenue"].assessment == "stable"
    assert by_name["capital_expenditure"].assessment == "contextual"
    assert by_name["financing_cash_flow"].direction == "turnaround"
    assert by_name["financing_cash_flow"].assessment == "contextual"
    assert "missing" not in by_name


def test_analyzes_ratio_change_in_percentage_points() -> None:
    movements = analyze_financial_performance(
        {},
        {
            "2025": {"operating_margin": Ratio("operating_margin", 20, "x")},
            "2024": {"operating_margin": Ratio("operating_margin", 15, "x")},
        },
    )

    movement = movements[0]
    assert movement.metric_type == "ratio"
    assert movement.unit == "percentage_points"
    assert movement.absolute_change == 5
    assert movement.assessment == "favorable"

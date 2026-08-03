from fris.agents.agent_06_insight_generation import generate_financial_insights
from fris.models import Evidence, FinancialMovement, RiskFinding


def _movement(
    name: str,
    *,
    change: float | None = 10,
    absolute: float = 10,
    assessment: str = "favorable",
    direction: str = "increased",
    current_period: str = "2025",
    evidence: Evidence | None = None,
) -> FinancialMovement:
    return FinancialMovement(
        name=name,
        category="Test",
        metric_type="fact",
        current_period=current_period,
        prior_period=str(int(current_period) - 1),
        current_value=110,
        prior_value=100,
        absolute_change=absolute,
        percentage_change=change,
        direction=direction,
        assessment=assessment,
        rationale="test",
        evidence=evidence,
    )


def _risk(metric: str, severity: str = "high") -> RiskFinding:
    return RiskFinding(
        code=f"risk_{metric}",
        title="Test risk",
        category="Test",
        severity=severity,
        period="2025",
        metric=metric,
        observed_value=1,
        trigger="test",
        implication="test",
        suggested_action="test",
    )


def test_generates_traceable_insight_and_links_risk() -> None:
    evidence = Evidence(page=42, text="Revenue 110 100")
    insights = generate_financial_insights(
        [_movement("revenue", assessment="adverse", direction="decreased", change=-10, evidence=evidence)],
        [_risk("revenue")],
    )

    insight = insights[0]
    assert insight.priority == "high"
    assert insight.related_risks == ("risk_revenue",)
    assert insight.evidence == (evidence,)
    assert "decreased by 10.00%" in insight.narrative
    assert "Investigate" not in insight.business_meaning
    assert "volume" in insight.investigation.lower()


def test_does_not_assert_an_unverified_cause() -> None:
    insight = generate_financial_insights([_movement("net_income")], [])[0]

    assert "caused by" not in insight.narrative.lower()
    assert "caused by" not in insight.business_meaning.lower()
    assert "separate" in insight.investigation.lower()


def test_uses_latest_period_and_excludes_stable_or_contextual_movements() -> None:
    insights = generate_financial_insights(
        [
            _movement("revenue", current_period="2024"),
            _movement("net_income", current_period="2025"),
            _movement("total_debt", current_period="2025", assessment="stable", direction="stable"),
            _movement("capital_expenditure", current_period="2025", assessment="contextual"),
        ],
        [],
    )

    assert [insight.related_metrics for insight in insights] == [("net_income",)]


def test_ranks_high_risk_first_and_respects_limit() -> None:
    insights = generate_financial_insights(
        [
            _movement("revenue"),
            _movement("total_debt", assessment="adverse", change=25),
            _movement("net_income", assessment="adverse", change=-5, direction="decreased"),
        ],
        [_risk("total_debt")],
        limit=2,
    )

    assert len(insights) == 2
    assert insights[0].related_metrics == ("total_debt",)
    assert insights[0].priority == "high"


def test_returns_no_insights_without_comparable_movements() -> None:
    assert generate_financial_insights([], []) == []
    assert generate_financial_insights([_movement("revenue")], [], limit=0) == []

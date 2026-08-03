import json
from pathlib import Path

import pytest

from fris import ExtractionMode, FinancialReportPipeline
from fris.agents.agent_01_document_processing import ModelStatus
from fris.agents.agent_06_insight_generation import (
    NarrativeAugmentationError,
    augment_financial_insights,
)
from fris.models import Evidence, FinancialInsight, RiskFinding


SAMPLES = Path(__file__).resolve().parents[2] / "sample_reports"


class FakeNarrativeProvider:
    model = "fake-narrative"

    def __init__(self, payload: dict, available: bool = True) -> None:
        self.payload = payload
        self.available = available
        self.prompt = ""
        self.schema = {}

    def status(self) -> ModelStatus:
        return ModelStatus(self.available, self.model, "ready" if self.available else "missing")

    def generate(self, prompt: str, schema: dict) -> str:
        self.prompt = prompt
        self.schema = schema
        return json.dumps(self.payload)


class AdaptiveNarrativeProvider(FakeNarrativeProvider):
    def __init__(self) -> None:
        super().__init__({})

    def generate(self, prompt: str, schema: dict) -> str:
        source = json.loads(prompt.split("VALIDATED_INPUT:\n", 1)[1])
        return json.dumps(
            {
                "themes": [
                    {
                        "theme_id": item["theme_id"],
                        "title": item["suggested_title"],
                        "priority": item["priority"],
                        "narrative": (
                            ", ".join(metric.replace("_", " ").title() for metric in item["metrics"])
                            + " should be reviewed together."
                        ),
                        "business_meaning": "The combined movements change financial flexibility.",
                        "investigation": "Review the supplied movements and report notes together.",
                    }
                    for item in source["validated_themes"]
                ]
            }
        )


def _insight() -> FinancialInsight:
    return FinancialInsight(
        code="movement_revenue_2025",
        title="Revenue: increased",
        category="Performance",
        priority="low",
        sentiment="favorable",
        current_period="2025",
        prior_period="2024",
        narrative="Revenue increased by 12.38%, moving from 637,959.00 in 2024 to 716,924.00 in 2025.",
        business_meaning="This indicates top-line growth.",
        investigation="Review price, volume, and mix.",
        related_metrics=("revenue",),
        related_risks=("revenue_risk",),
        evidence=(Evidence(48, "Revenue 716,924 637,959"),),
    )


def _risk() -> RiskFinding:
    return RiskFinding(
        code="revenue_risk",
        title="Revenue risk",
        category="Performance",
        severity="medium",
        period="2025",
        metric="revenue",
        observed_value=12.38,
        trigger="test",
        implication="test",
        suggested_action="test",
        evidence=Evidence(48, "Revenue 716,924 637,959"),
    )


def _theme(**overrides) -> dict:
    theme = {
        "theme_id": "profitability",
        "title": "Revenue and growth",
        "priority": "low",
        "narrative": "Revenue increased by 12.4% in 2025.",
        "business_meaning": "Top-line scale improved.",
        "investigation": "Review price, volume, and mix.",
    }
    theme.update(overrides)
    return theme


def test_accepts_verified_structured_model_theme() -> None:
    provider = FakeNarrativeProvider({"themes": [_theme()]})

    themes = augment_financial_insights([_insight()], [_risk()], provider)

    assert themes[0].related_metrics == ("revenue",)
    assert themes[0].evidence_pages == (48,)
    assert "VALIDATED_INPUT" in provider.prompt
    assert provider.schema["properties"]["themes"]["maxItems"] == 6


def test_rejects_invented_figure() -> None:
    provider = FakeNarrativeProvider(
        {"themes": [_theme(narrative="Revenue increased by 999.00% in 2025.")]}
    )

    with pytest.raises(NarrativeAugmentationError, match="introduced a figure"):
        augment_financial_insights([_insight()], [_risk()], provider)


def test_rejects_unsupported_causal_claim() -> None:
    provider = FakeNarrativeProvider(
        {"themes": [_theme(narrative="Revenue increased due to stronger demand.")]}
    )

    with pytest.raises(NarrativeAugmentationError, match="causal claim"):
        augment_financial_insights([_insight()], [_risk()], provider)


def test_rejects_unknown_or_duplicate_theme() -> None:
    provider = FakeNarrativeProvider(
        {"themes": [_theme(theme_id="invented_theme")]}
    )
    with pytest.raises(NarrativeAugmentationError, match="unknown or duplicate theme"):
        augment_financial_insights([_insight()], [_risk()], provider)

    provider = FakeNarrativeProvider({"themes": [_theme(), _theme()]})
    with pytest.raises(NarrativeAugmentationError, match="unknown or duplicate theme"):
        augment_financial_insights([_insight()], [_risk()], provider)


def test_pipeline_uses_verified_augmentation_and_falls_back_safely() -> None:
    valid_provider = AdaptiveNarrativeProvider()
    result = FinancialReportPipeline(
        extraction_mode=ExtractionMode.RULES_ONLY,
        augment_insights=True,
        narrative_provider=valid_provider,
    ).analyze(SAMPLES / "Amazon-2025-Annual-Report.pdf")

    assert result.insight_model_used == "fake-narrative"
    assert result.augmented_insights
    assert {theme.title for theme in result.augmented_insights} >= {"Growth and profitability"}

    invalid_provider = FakeNarrativeProvider(
        {"themes": [_theme(narrative="Revenue increased by 999.00% in 2025.")]}
    )
    fallback = FinancialReportPipeline(
        extraction_mode=ExtractionMode.RULES_ONLY,
        augment_insights=True,
        narrative_provider=invalid_provider,
    ).analyze(SAMPLES / "Amazon-2025-Annual-Report.pdf")

    assert fallback.augmented_insights == []
    assert fallback.insight_model_used is None
    assert any("rejected by verification" in warning for warning in fallback.warnings)

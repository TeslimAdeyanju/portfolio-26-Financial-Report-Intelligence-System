"""Insight Generation Agent public interface."""

from .insights import generate_financial_insights
from .narrative import (
    DEFAULT_NARRATIVE_MODEL,
    InsightNarrativeProvider,
    NarrativeAugmentationError,
    OllamaNarrativeProvider,
    augment_financial_insights,
)

__all__ = [
    "DEFAULT_NARRATIVE_MODEL",
    "InsightNarrativeProvider",
    "NarrativeAugmentationError",
    "OllamaNarrativeProvider",
    "augment_financial_insights",
    "generate_financial_insights",
]

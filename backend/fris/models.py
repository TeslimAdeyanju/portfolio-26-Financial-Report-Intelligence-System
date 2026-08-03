"""Typed domain models used throughout the Version 1 pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Evidence:
    page: int
    text: str


@dataclass(frozen=True)
class Metric:
    name: str
    value: float
    unit: str = "currency"
    confidence: float = 0.0
    evidence: Evidence | None = None


@dataclass(frozen=True)
class Ratio:
    name: str
    value: float
    formula: str


@dataclass(frozen=True)
class StatementRow:
    name: str
    values: dict[str, float]
    evidence: Evidence
    label: str = ""
    section: str | None = None
    extraction_method: str = "deterministic"
    confidence: float = 1.0


@dataclass(frozen=True)
class FinancialStatement:
    name: str
    periods: tuple[str, ...]
    rows: dict[str, StatementRow]
    currency: str
    unit: str
    unit_scale: int
    page: int
    sections: tuple[str, ...] = ()
    extraction_method: str = "deterministic"
    confidence: float = 1.0


@dataclass(frozen=True)
class FinancialFact:
    name: str
    category: str
    values: dict[str, float]
    source_label: str = ""
    currency: str = "unknown"
    unit: str = "units"
    unit_scale: int = 1
    status: str = "reported"
    reason: str | None = None
    evidence: Evidence | None = None
    extraction_method: str = "deterministic"
    confidence: float = 1.0


@dataclass(frozen=True)
class FinancialMovement:
    name: str
    category: str
    metric_type: str
    current_period: str
    prior_period: str
    current_value: float
    prior_value: float
    absolute_change: float
    percentage_change: float | None
    direction: str
    assessment: str
    rationale: str
    currency: str = "unknown"
    unit: str = "units"
    evidence: Evidence | None = None


@dataclass(frozen=True)
class RiskFinding:
    code: str
    title: str
    category: str
    severity: str
    period: str
    metric: str
    observed_value: float
    trigger: str
    implication: str
    suggested_action: str
    unit: str = "units"
    evidence: Evidence | None = None


@dataclass(frozen=True)
class FinancialInsight:
    code: str
    title: str
    category: str
    priority: str
    sentiment: str
    current_period: str
    prior_period: str
    narrative: str
    business_meaning: str
    investigation: str
    related_metrics: tuple[str, ...]
    related_risks: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()


@dataclass(frozen=True)
class AugmentedInsight:
    title: str
    priority: str
    narrative: str
    business_meaning: str
    investigation: str
    related_metrics: tuple[str, ...]
    related_risks: tuple[str, ...] = ()
    evidence_pages: tuple[int, ...] = ()


@dataclass(frozen=True)
class ValidationResult:
    name: str
    period: str
    passed: bool
    formula: str
    actual: float
    expected: float
    difference: float


@dataclass
class AnalysisResult:
    source_file: str
    page_count: int
    metrics: dict[str, Metric] = field(default_factory=dict)
    ratios: dict[str, Ratio] = field(default_factory=dict)
    statements: dict[str, FinancialStatement] = field(default_factory=dict)
    financial_facts: dict[str, FinancialFact] = field(default_factory=dict)
    financial_movements: list[FinancialMovement] = field(default_factory=list)
    risk_findings: list[RiskFinding] = field(default_factory=list)
    financial_insights: list[FinancialInsight] = field(default_factory=list)
    augmented_insights: list[AugmentedInsight] = field(default_factory=list)
    period_ratios: dict[str, dict[str, Ratio]] = field(default_factory=dict)
    validations: list[ValidationResult] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    extraction_mode: str = "rules_only"
    model_used: str | None = None
    insight_model_used: str | None = None
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

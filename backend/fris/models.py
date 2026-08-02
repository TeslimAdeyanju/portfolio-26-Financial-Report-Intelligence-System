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


@dataclass(frozen=True)
class FinancialStatement:
    name: str
    periods: tuple[str, ...]
    rows: dict[str, StatementRow]
    currency: str
    unit: str
    unit_scale: int
    page: int


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
    period_ratios: dict[str, dict[str, Ratio]] = field(default_factory=dict)
    validations: list[ValidationResult] = field(default_factory=list)
    summary: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

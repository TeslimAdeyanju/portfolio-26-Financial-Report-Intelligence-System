"""Version 1 orchestration pipeline."""

from __future__ import annotations

from pathlib import Path

from .agents.data_quality_agent import validate_financials
from .agents.document_processing_agent import (
    extract_pdf,
    extract_statement_pages_with_ocr,
    text_quality_issue,
)
from .agents.metrics_extraction_agent import (
    extract_metrics,
    extract_statements,
    select_primary_statement_pages,
)
from .agents.narrative_synthesis_agent import generate_summary
from .agents.financial_calculation_engine import calculate_period_ratios, calculate_ratios
from .models import AnalysisResult, Metric


_LATEST_METRIC_ROWS = {
    "revenue": ("income_statement", "revenue"),
    "gross_profit": ("income_statement", "gross_profit"),
    "operating_profit": ("income_statement", "operating_income"),
    "net_income": ("income_statement", "net_income"),
    "current_assets": ("balance_sheet", "current_assets"),
    "current_liabilities": ("balance_sheet", "current_liabilities"),
    "total_assets": ("balance_sheet", "total_assets"),
    "total_equity": ("balance_sheet", "total_equity"),
    "total_debt": ("balance_sheet", "total_debt"),
}


def _latest_metrics(statements):
    metrics: dict[str, Metric] = {}
    for metric_name, (statement_name, row_name) in _LATEST_METRIC_ROWS.items():
        statement = statements.get(statement_name)
        if not statement or row_name not in statement.rows:
            continue
        period = statement.periods[0]
        row = statement.rows[row_name]
        value = row.values.get(period)
        if value is not None:
            metrics[metric_name] = Metric(
                metric_name,
                value,
                unit=f"{statement.currency} {statement.unit}",
                confidence=0.9,
                evidence=row.evidence,
            )
    return metrics


class FinancialReportPipeline:
    def analyze(self, source: str | Path | bytes, filename: str | None = None) -> AnalysisResult:
        pages = extract_pdf(source)
        quality_issue = text_quality_issue(pages)
        analysis_pages = pages
        warnings: list[str] = []
        if quality_issue:
            analysis_pages = extract_statement_pages_with_ocr(source)
            warnings.append(
                f"{quality_issue} Two-pass OCR fallback was applied to primary statements."
            )
        statement_pages = select_primary_statement_pages(analysis_pages)
        statements = extract_statements(statement_pages)
        metrics = _latest_metrics(statements) or extract_metrics(statement_pages)
        period_ratios = calculate_period_ratios(statements)
        latest_period = next(iter(period_ratios), None)
        ratios = period_ratios.get(latest_period, {}) if latest_period else calculate_ratios(metrics)
        validations = validate_financials(statements, period_ratios)
        if not metrics:
            warnings.append(
                "No supported metrics were confidently extracted from the document text."
            )
        return AnalysisResult(
            source_file=filename or (Path(source).name if not isinstance(source, bytes) else "upload.pdf"),
            page_count=len(pages),
            metrics=metrics,
            ratios=ratios,
            statements=statements,
            period_ratios=period_ratios,
            validations=validations,
            summary=generate_summary(metrics, ratios),
            warnings=warnings,
        )

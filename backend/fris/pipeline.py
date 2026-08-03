"""Version 1 orchestration pipeline."""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from .agents.agent_01_document_processing import (
    DEFAULT_GLM_OCR_MODEL,
    DEFAULT_OLLAMA_URL,
    ModelOCRProvider,
    ModelStatus,
    OllamaError,
    OllamaGLMOCRProvider,
    extract_pages_with_model,
    extract_pdf,
    extract_statement_pages_with_ocr,
    text_quality_issue,
)
from .agents.agent_02_metrics_extraction import (
    extract_financial_facts,
    extract_metrics,
    extract_statements,
    select_primary_statement_pages,
)
from .agents.agent_03_financial_calculation_engine import (
    calculate_period_ratios,
    calculate_ratios,
)
from .agents.agent_04_data_quality import validate_financials
from .agents.agent_05_financial_analysis import analyze_financial_performance
from .agents.agent_06_insight_generation import (
    DEFAULT_NARRATIVE_MODEL,
    InsightNarrativeProvider,
    NarrativeAugmentationError,
    OllamaNarrativeProvider,
    augment_financial_insights,
    generate_financial_insights,
)
from .agents.agent_07_risk_assessment import assess_financial_risks
from .agents.agent_09_narrative_synthesis import generate_summary
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

_MINIMUM_COMPLETE_ROWS = {
    "income_statement": 8,
    "balance_sheet": 12,
    "cash_flow_statement": 12,
}


class ExtractionMode(str, Enum):
    AUTOMATIC = "automatic"
    MODEL_ASSISTED = "model_assisted"
    RULES_ONLY = "rules_only"


def _latest_metrics(statements):
    metrics: dict[str, Metric] = {}
    for metric_name, (statement_name, row_name) in _LATEST_METRIC_ROWS.items():
        statement = statements.get(statement_name)
        if not statement or row_name not in statement.rows:
            continue
        period = max(statement.periods, key=lambda value: int(value) if value.isdigit() else value)
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
    def __init__(
        self,
        *,
        extraction_mode: ExtractionMode | str = ExtractionMode.AUTOMATIC,
        model_provider: ModelOCRProvider | None = None,
        ollama_url: str = DEFAULT_OLLAMA_URL,
        model_name: str = DEFAULT_GLM_OCR_MODEL,
        model_timeout: float = 300,
        model_dpi: int = 144,
        augment_insights: bool = False,
        narrative_provider: InsightNarrativeProvider | None = None,
        narrative_model_name: str = DEFAULT_NARRATIVE_MODEL,
        narrative_timeout: float = 600,
    ) -> None:
        try:
            self.extraction_mode = ExtractionMode(extraction_mode)
        except ValueError as exc:
            allowed = ", ".join(mode.value for mode in ExtractionMode)
            raise ValueError(f"Unknown extraction mode. Choose one of: {allowed}") from exc
        self.model_provider = model_provider or OllamaGLMOCRProvider(
            base_url=ollama_url,
            model=model_name,
            timeout=model_timeout,
        )
        self.model_dpi = model_dpi
        self.augment_insights = augment_insights
        self.narrative_provider = narrative_provider or OllamaNarrativeProvider(
            base_url=ollama_url,
            model=narrative_model_name,
            timeout=narrative_timeout,
        )

    def model_status(self) -> ModelStatus:
        return self.model_provider.status()

    def narrative_model_status(self) -> ModelStatus:
        return self.narrative_provider.status()

    @staticmethod
    def _needs_model_assistance(statements, validations) -> bool:
        for name, minimum_rows in _MINIMUM_COMPLETE_ROWS.items():
            statement = statements.get(name)
            if statement is None or len(statement.rows) < minimum_rows:
                return True
        return any(not validation.passed for validation in validations)

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

        statement_pages = select_primary_statement_pages(analysis_pages, fallback=False)
        model_candidate_pages = statement_pages
        statements = extract_statements(statement_pages)
        period_ratios = calculate_period_ratios(statements)
        validations = validate_financials(statements, period_ratios)

        use_model = self.extraction_mode is ExtractionMode.MODEL_ASSISTED or (
            self.extraction_mode is ExtractionMode.AUTOMATIC
            and self._needs_model_assistance(statements, validations)
        )
        model_used: str | None = None
        if use_model:
            status = self.model_provider.status()
            if not model_candidate_pages:
                warnings.append(
                    "Model assistance was requested, but no primary financial-statement "
                    "pages were confidently identified. Rules-based extraction was retained."
                )
            elif not status.available:
                warnings.append(
                    f"Model assistance was requested but unavailable: {status.detail} "
                    "Rules-based extraction was retained."
                )
            else:
                try:
                    model_pages = extract_pages_with_model(
                        source,
                        model_candidate_pages,
                        self.model_provider,
                        dpi=self.model_dpi,
                    )
                    assisted_statements = extract_statements([*statement_pages, *model_pages])
                    if assisted_statements:
                        statements = assisted_statements
                        period_ratios = calculate_period_ratios(statements)
                        validations = validate_financials(statements, period_ratios)
                        model_used = status.model
                        warnings.append(
                            f"GLM-OCR model assistance processed {len(model_pages)} "
                            "financial-statement page(s). All figures were revalidated."
                        )
                    else:
                        warnings.append(
                            "GLM-OCR returned no parseable statements; rules-based "
                            "extraction was retained."
                        )
                except (OllamaError, RuntimeError, ValueError) as exc:
                    warnings.append(
                        f"GLM-OCR could not complete extraction: {exc} "
                        "Rules-based extraction was retained."
                    )

        metrics = _latest_metrics(statements) or extract_metrics(statement_pages)
        financial_facts = extract_financial_facts(statements)
        financial_movements = analyze_financial_performance(financial_facts, period_ratios)
        latest_period = (
            max(period_ratios, key=lambda value: int(value) if value.isdigit() else value)
            if period_ratios
            else None
        )
        ratios = period_ratios.get(latest_period, {}) if latest_period else calculate_ratios(metrics)
        risk_findings = assess_financial_risks(
            financial_facts, period_ratios, financial_movements, validations
        )
        financial_insights = generate_financial_insights(
            financial_movements, risk_findings
        )
        augmented_insights = []
        insight_model_used: str | None = None
        if self.augment_insights and financial_insights:
            narrative_status = self.narrative_provider.status()
            if not narrative_status.available:
                warnings.append(
                    f"Insight augmentation was requested but unavailable: "
                    f"{narrative_status.detail} Deterministic insights were retained."
                )
            else:
                try:
                    augmented_insights = augment_financial_insights(
                        financial_insights, risk_findings, self.narrative_provider
                    )
                    insight_model_used = narrative_status.model
                except NarrativeAugmentationError as exc:
                    warnings.append(
                        f"Insight augmentation was rejected by verification: {exc} "
                        "Deterministic insights were retained."
                    )
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
            financial_facts=financial_facts,
            financial_movements=financial_movements,
            risk_findings=risk_findings,
            financial_insights=financial_insights,
            augmented_insights=augmented_insights,
            period_ratios=period_ratios,
            validations=validations,
            summary=generate_summary(metrics, ratios),
            warnings=warnings,
            extraction_mode=self.extraction_mode.value,
            model_used=model_used,
            insight_model_used=insight_model_used,
        )

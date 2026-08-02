from __future__ import annotations

import fitz

from fris import ExtractionMode, FinancialReportPipeline
from fris.agents.agent_01_document_processing import (
    ModelStatus,
    PageText,
    extract_pages_with_model,
    normalize_model_table,
)
from fris.agents.agent_02_metrics_extraction import extract_statements


MODEL_TABLE = """
| Row | 2025 | 2024 |
| --- | ---: | ---: |
| Revenue | 1,000 | 900 |
| Cost of sales | 600 | 550 |
| Gross profit | 400 | 350 |
| Operating expenses | 200 | 180 |
| Operating income | 200 | 170 |
| Income before provision for income taxes | 180 | 150 |
| Provision for income taxes | 40 | 35 |
| Net income | 140 | 115 |
"""


class FakeProvider:
    model = "glm-ocr:test"

    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.images: list[bytes] = []

    def status(self) -> ModelStatus:
        return ModelStatus(self.available, self.model, "ready" if self.available else "offline")

    def extract_page(self, image: bytes) -> str:
        self.images.append(image)
        return MODEL_TABLE


def _income_pdf() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (72, 72),
        "CONSOLIDATED STATEMENTS OF INCOME\n"
        "USD ($ in millions)\n"
        "2025 2024\n"
        "Revenue 1,000 900",
    )
    payload = document.tobytes()
    document.close()
    return payload


def test_normalizes_markdown_and_html_tables() -> None:
    markdown = normalize_model_table(MODEL_TABLE)
    html = normalize_model_table(
        "<table><tr><th>Row</th><th>2025</th></tr>"
        "<tr><td>Revenue</td><td>1,000</td></tr></table>"
    )

    assert "Revenue 1,000 900" in markdown
    assert "---" not in markdown
    assert html == "Row 2025\nRevenue 1,000"


def test_renders_and_extracts_model_page_with_provenance() -> None:
    provider = FakeProvider()
    pages = [
        PageText(
            1,
            "CONSOLIDATED STATEMENTS OF INCOME\n"
            "USD ($ in millions)\n2025 2024",
        )
    ]

    extracted = extract_pages_with_model(_income_pdf(), pages, provider)
    statements = extract_statements(extracted)

    assert provider.images[0].startswith(b"\x89PNG")
    assert extracted[0].method == "ollama:glm-ocr:test"
    assert statements["income_statement"].rows["revenue"].values["2025"] == 1_000
    assert statements["income_statement"].extraction_method == "ollama:glm-ocr:test"


def test_pipeline_model_assisted_mode_uses_provider_and_revalidates() -> None:
    provider = FakeProvider()

    result = FinancialReportPipeline(
        extraction_mode=ExtractionMode.MODEL_ASSISTED,
        model_provider=provider,
    ).analyze(_income_pdf(), "income.pdf")

    assert result.model_used == "glm-ocr:test"
    assert result.extraction_mode == "model_assisted"
    assert len(result.statements["income_statement"].rows) >= 8
    assert result.statements["income_statement"].rows["net_income"].values["2025"] == 140
    assert any("All figures were revalidated" in warning for warning in result.warnings)


def test_model_failure_falls_back_without_losing_rules_output() -> None:
    result = FinancialReportPipeline(
        extraction_mode=ExtractionMode.MODEL_ASSISTED,
        model_provider=FakeProvider(available=False),
    ).analyze(_income_pdf(), "income.pdf")

    assert result.model_used is None
    assert result.statements["income_statement"].rows["revenue"].values["2025"] == 1_000
    assert any("Rules-based extraction was retained" in warning for warning in result.warnings)

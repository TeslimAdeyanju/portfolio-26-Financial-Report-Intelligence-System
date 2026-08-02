"""Metrics Extraction Agent: conservative, evidence-backed extraction."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ...models import Evidence, Metric
from ..document_processing_agent.processor import PageText


METRIC_LABELS: dict[str, tuple[str, ...]] = {
    "revenue": ("total net sales", "revenue", "turnover", "total sales"),
    "gross_profit": ("gross profit", "gross margin"),
    "operating_profit": ("operating profit", "operating income"),
    "net_income": ("net income", "profit for the year", "net profit"),
    "current_assets": ("total current assets",),
    "current_liabilities": ("total current liabilities",),
    "total_assets": ("total assets",),
    "total_equity": (
        "total equity",
        "total shareholders' equity",
        "total shareholders’ equity",
        "shareholders' equity",
        "stockholders' equity",
    ),
    "total_debt": ("total debt", "borrowings"),
}

_NUMBER = r"(?P<value>\(?[-+]?\s*(?:[$£€]\s*)?\d[\d,]*(?:\.\d+)?\)?)"


def _parse_number(raw: str) -> float:
    value = re.sub(r"[$£€,\s]", "", raw)
    negative = value.startswith("(") and value.endswith(")")
    value = value.strip("()")
    number = float(value)
    return -number if negative else number


def extract_metrics(pages: Iterable[PageText]) -> dict[str, Metric]:
    """Find the first strong label/value match for each supported metric."""
    found: dict[str, Metric] = {}
    for page in pages:
        lines = [" ".join(line.split()) for line in page.text.splitlines()]
        for index, compact in enumerate(lines):
            for name, labels in METRIC_LABELS.items():
                if name in found:
                    continue
                label_pattern = "|".join(re.escape(label) for label in labels)
                match = re.search(
                    rf"\b(?:{label_pattern})\b\s*[:\-]?\s*{_NUMBER}", compact,
                    flags=re.IGNORECASE,
                )
                evidence_text = compact
                if not match and re.fullmatch(
                    rf"\s*(?:{label_pattern})\s*[:\-]?\s*",
                    compact,
                    flags=re.IGNORECASE,
                ):
                    evidence_text = " ".join(lines[index : index + 5])
                    match = re.search(_NUMBER, " ".join(lines[index + 1 : index + 5]))
                if match:
                    found[name] = Metric(
                        name=name,
                        value=_parse_number(match.group("value")),
                        confidence=0.8,
                        evidence=Evidence(page=page.number, text=evidence_text[:500]),
                    )
    return found


_STATEMENT_HEADINGS = (
    "consolidated statements of operations",
    "consolidated statement of operations",
    "income statement",
    "statement of profit or loss",
    "consolidated balance sheets",
    "consolidated balance sheet",
    "statement of financial position",
    "consolidated statements of cash flows",
    "consolidated statement of cash flows",
    "cash flow statement",
)


def select_primary_statement_pages(pages: Iterable[PageText]) -> list[PageText]:
    """Prefer audited primary statements over narrative metric mentions."""
    page_list = list(pages)
    selected = [
        page
        for page in page_list
        if any(heading in page.text.lower() for heading in _STATEMENT_HEADINGS)
    ]
    return selected or page_list

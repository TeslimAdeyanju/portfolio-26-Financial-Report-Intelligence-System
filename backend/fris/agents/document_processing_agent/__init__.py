"""Document Processing Agent public interface."""

from .processor import (
    PageText,
    extract_pdf,
    extract_pdf_with_ocr,
    extract_statement_pages_with_ocr,
    text_quality_issue,
)

__all__ = [
    "PageText",
    "extract_pdf",
    "extract_pdf_with_ocr",
    "extract_statement_pages_with_ocr",
    "text_quality_issue",
]

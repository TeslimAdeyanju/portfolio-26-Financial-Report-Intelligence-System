"""Document Processing Agent public interface."""

from .processor import (
    PageText,
    extract_pdf,
    extract_pdf_with_ocr,
    extract_statement_pages_with_ocr,
    is_primary_statement,
    text_quality_issue,
)
from .ollama_ocr import (
    DEFAULT_GLM_OCR_MODEL,
    DEFAULT_OLLAMA_URL,
    ModelOCRProvider,
    ModelStatus,
    OllamaError,
    OllamaGLMOCRProvider,
    extract_pages_with_model,
    normalize_model_table,
    render_pdf_page,
)

__all__ = [
    "PageText",
    "extract_pdf",
    "extract_pdf_with_ocr",
    "extract_statement_pages_with_ocr",
    "is_primary_statement",
    "text_quality_issue",
    "DEFAULT_GLM_OCR_MODEL",
    "DEFAULT_OLLAMA_URL",
    "ModelOCRProvider",
    "ModelStatus",
    "OllamaError",
    "OllamaGLMOCRProvider",
    "extract_pages_with_model",
    "normalize_model_table",
    "render_pdf_page",
]

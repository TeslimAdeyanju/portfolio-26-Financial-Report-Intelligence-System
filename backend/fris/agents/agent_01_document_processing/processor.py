"""Document Processing Agent: PDF extraction with page-level traceability."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil


@dataclass(frozen=True)
class PageText:
    number: int
    text: str


def extract_pdf(source: str | Path | bytes) -> list[PageText]:
    """Extract text from a PDF path or byte payload."""
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError("PyMuPDF is required to read PDF files") from exc

    if isinstance(source, bytes):
        document = fitz.open(stream=source, filetype="pdf")
    else:
        document = fitz.open(str(source))

    try:
        return [
            PageText(number=index + 1, text=page.get_text("text"))
            for index, page in enumerate(document)
        ]
    finally:
        document.close()


def text_quality_issue(pages: list[PageText]) -> str | None:
    """Identify empty or corrupt embedded PDF text that requires OCR."""
    text = "".join(page.text for page in pages)
    if not text.strip():
        return "The PDF has no extractable text and requires OCR."

    control_characters = sum(
        ord(character) < 32 and character not in "\n\r\t" for character in text
    )
    if control_characters / len(text) > 0.02:
        return "The PDF's embedded text encoding is corrupt and requires OCR."
    return None


def _tessdata_directory() -> str:
    executable = shutil.which("tesseract")
    if executable is None:
        raise RuntimeError(
            "Tesseract OCR is required for this PDF. Install it with "
            "`brew install tesseract` on macOS or your system package manager."
        )
    executable_path = Path(executable).resolve()
    candidates = (
        Path(os.environ["TESSDATA_PREFIX"])
        if os.environ.get("TESSDATA_PREFIX")
        else None,
        executable_path.parents[1] / "share" / "tessdata",
        Path("/opt/homebrew/share/tessdata"),
        Path("/usr/local/share/tessdata"),
        Path("/usr/share/tesseract-ocr/5/tessdata"),
        Path("/usr/share/tesseract-ocr/4.00/tessdata"),
    )
    for candidate in candidates:
        if candidate and (candidate / "eng.traineddata").is_file():
            return str(candidate)
    raise RuntimeError(
        "Tesseract is installed but its English language data could not be found. "
        "Set TESSDATA_PREFIX to the tessdata directory."
    )


def extract_pdf_with_ocr(
    source: str | Path | bytes,
    *,
    language: str = "eng",
    dpi: int = 120,
) -> list[PageText]:
    """Render and OCR every page while preserving original page numbers."""
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError("PyMuPDF is required to OCR PDF files") from exc

    if isinstance(source, bytes):
        document = fitz.open(stream=source, filetype="pdf")
    else:
        document = fitz.open(str(source))

    tessdata = _tessdata_directory()
    try:
        pages: list[PageText] = []
        for index, page in enumerate(document):
            text_page = page.get_textpage_ocr(
                language=language,
                dpi=dpi,
                full=True,
                tessdata=tessdata,
            )
            pages.append(
                PageText(
                    number=index + 1,
                    text=page.get_text("text", textpage=text_page),
                )
            )
        return pages
    finally:
        document.close()


_PRIMARY_STATEMENT_MARKERS = (
    "consolidatedstatementsofoperations",
    "consolidatedstatementofoperations",
    "incomestatement",
    "consolidatedstatementsofincome",
    "consolidatedstatementofincome",
    "statementofprofitorloss",
    "consolidatedbalancesheets",
    "consolidatedbalancesheet",
    "statementoffinancialposition",
    "consolidatedstatementsofcashflows",
    "consolidatedstatementofcashflows",
    "cashflowstatement",
)


def _is_primary_statement(text: str) -> bool:
    # Audited statement titles appear at the top of a page. Limiting the search
    # prevents notes that merely reference a statement from being misclassified.
    normalized = "".join(
        character for character in text[:500].lower() if character.isalnum()
    )
    return any(marker in normalized for marker in _PRIMARY_STATEMENT_MARKERS)


def extract_statement_pages_with_ocr(
    source: str | Path | bytes,
    *,
    language: str = "eng",
    classification_dpi: int = 72,
    extraction_dpi: int = 200,
) -> list[PageText]:
    """Classify cheaply, then OCR only primary financial statements in detail."""
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError("PyMuPDF is required to OCR PDF files") from exc

    if isinstance(source, bytes):
        document = fitz.open(stream=source, filetype="pdf")
    else:
        document = fitz.open(str(source))

    tessdata = _tessdata_directory()
    try:
        selected_indexes: list[int] = []
        classified_pages: list[PageText] = []
        for index, page in enumerate(document):
            text_page = page.get_textpage_ocr(
                language=language,
                dpi=classification_dpi,
                full=True,
                tessdata=tessdata,
            )
            text = page.get_text("text", textpage=text_page)
            classified_pages.append(PageText(number=index + 1, text=text))
            if _is_primary_statement(text):
                selected_indexes.append(index)

        if not selected_indexes:
            return classified_pages

        detailed_pages: list[PageText] = []
        for index in selected_indexes:
            page = document[index]
            text_page = page.get_textpage_ocr(
                language=language,
                dpi=extraction_dpi,
                full=True,
                tessdata=tessdata,
            )
            detailed_pages.append(
                PageText(index + 1, page.get_text("text", textpage=text_page))
            )
        return detailed_pages
    finally:
        document.close()

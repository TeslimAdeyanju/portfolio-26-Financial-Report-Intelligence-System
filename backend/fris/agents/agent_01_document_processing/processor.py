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
    method: str = "embedded_text"
    confidence: float = 1.0


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
                    method="tesseract_ocr",
                    confidence=0.75,
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
    "statementsoffinancialposition",
    "groupincomestatement",
    "consolidatedstatementsofcashflows",
    "consolidatedstatementofcashflows",
    "cashflowstatement",
    "statementsofcashflows",
)


def is_primary_statement(text: str) -> bool:
    """Recognize an audited statement title without selecting indexes or notes."""
    top = " ".join(text[:1_000].casefold().split())
    if any(
        phrase in top
        for phrase in (
            "index to financial statements",
            "report of independent registered public accounting firm",
            "independent auditor's report",
            "independent auditor’s report",
            "reflected in the consolidated statements",
            "notes to consolidated financial statements",
            "notes to the financial statements",
        )
    ):
        return False

    nonempty_lines = [line for line in text.splitlines() if line.strip()]
    lines = [
        "".join(character for character in line.casefold() if character.isalnum())
        for line in nonempty_lines[:6]
    ]
    for line in lines:
        for marker in _PRIMARY_STATEMENT_MARKERS:
            position = line.find(marker)
            if position < 0 or position > 80:
                continue
            suffix = line[position + len(marker) :]
            if suffix.startswith("isasfollows"):
                continue
            if len(suffix) <= 100:
                return True
    return False


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
            classified_pages.append(
                PageText(
                    number=index + 1,
                    text=text,
                    method="tesseract_classification",
                    confidence=0.6,
                )
            )
            if is_primary_statement(text):
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
                PageText(
                    index + 1,
                    page.get_text("text", textpage=text_page),
                    method="tesseract_ocr",
                    confidence=0.75,
                )
            )
        return detailed_pages
    finally:
        document.close()

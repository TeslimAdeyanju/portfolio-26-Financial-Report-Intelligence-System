"""Local GLM-OCR integration through Ollama's native vision endpoint."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .processor import PageText


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_GLM_OCR_MODEL = "glm-ocr:latest"


class ModelOCRProvider(Protocol):
    """Small provider contract so other local or hosted OCR models can be added later."""

    model: str

    def status(self) -> "ModelStatus": ...

    def extract_page(self, image: bytes) -> str: ...


@dataclass(frozen=True)
class ModelStatus:
    available: bool
    model: str
    detail: str


class OllamaError(RuntimeError):
    """Raised when Ollama cannot complete a model request."""


class OllamaGLMOCRProvider:
    """Call GLM-OCR sequentially through Ollama's native `/api/generate` API."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_GLM_OCR_MODEL,
        timeout: float = 300,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _request(self, path: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if data is not None else "GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise OllamaError(f"Ollama returned HTTP {exc.code}: {body[:300]}") from exc
        except URLError as exc:
            raise OllamaError(
                f"Ollama is unavailable at {self.base_url}. Start it before using "
                "model-assisted extraction."
            ) from exc
        except (TimeoutError, json.JSONDecodeError) as exc:
            raise OllamaError(f"Ollama returned an invalid or timed-out response: {exc}") from exc

    def status(self) -> ModelStatus:
        try:
            payload = self._request("/api/tags")
        except OllamaError as exc:
            return ModelStatus(False, self.model, str(exc))
        installed = {
            item.get("name") or item.get("model")
            for item in payload.get("models", [])
            if isinstance(item, dict)
        }
        aliases = {self.model, self.model.removesuffix(":latest")}
        if not installed.intersection(aliases):
            return ModelStatus(
                False,
                self.model,
                f"Model {self.model!r} is not installed. Run `ollama pull {self.model}`.",
            )
        return ModelStatus(True, self.model, "Ollama and GLM-OCR are ready.")

    def extract_page(self, image: bytes) -> str:
        payload = self._request(
            "/api/generate",
            {
                "model": self.model,
                "prompt": "Table Recognition:",
                "images": [base64.b64encode(image).decode("ascii")],
                "stream": False,
                "options": {"temperature": 0},
                "keep_alive": "2m",
            },
        )
        output = payload.get("response")
        if not isinstance(output, str) or not output.strip():
            raise OllamaError("GLM-OCR returned an empty page response.")
        return output


class _HTMLTableReader(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(self._row):
                self.rows.append(self._row)
            self._row = None


def normalize_model_table(text: str) -> str:
    """Convert GLM-OCR HTML/Markdown tables into parser-friendly text rows."""
    cleaned = re.sub(r"^```(?:html|markdown)?\s*|\s*```$", "", text.strip(), flags=re.I)
    if re.search(r"<table\b", cleaned, flags=re.I):
        reader = _HTMLTableReader()
        reader.feed(cleaned)
        table_text = "\n".join(" ".join(cell for cell in row if cell) for row in reader.rows)
        outside = re.sub(r"<table\b.*?</table>", "", cleaned, flags=re.I | re.S)
        outside = re.sub(r"<[^>]+>", " ", outside)
        cleaned = "\n".join(part for part in (outside.strip(), table_text) if part)

    lines: list[str] = []
    for line in cleaned.splitlines():
        compact = line.strip()
        if compact.startswith("|") and compact.endswith("|"):
            cells = [cell.strip() for cell in compact.strip("|").split("|")]
            if cells and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                continue
            compact = " ".join(cell for cell in cells if cell)
        compact = re.sub(r"<[^>]+>", " ", compact)
        compact = " ".join(compact.split())
        if compact:
            lines.append(compact)
    return "\n".join(lines)


def render_pdf_page(
    source: str | Path | bytes,
    page_number: int,
    *,
    dpi: int = 144,
) -> bytes:
    """Render one one-based PDF page as PNG for sequential vision inference."""
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError("PyMuPDF is required to render PDF pages") from exc

    document = (
        fitz.open(stream=source, filetype="pdf")
        if isinstance(source, bytes)
        else fitz.open(str(source))
    )
    try:
        if page_number < 1 or page_number > len(document):
            raise ValueError(f"PDF page {page_number} is outside 1-{len(document)}")
        page = document[page_number - 1]
        scale = dpi / 72
        return page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes("png")
    finally:
        document.close()


def _context_header(text: str) -> str:
    """Retain deterministic title/unit/period metadata around a model table."""
    selected: list[str] = []
    for line in (" ".join(item.split()) for item in text.splitlines() if item.strip()):
        lowered = line.casefold()
        if (
            "statement" in lowered
            or "balance sheet" in lowered
            or "in million" in lowered
            or "in thousand" in lowered
            or "in billion" in lowered
            or re.fullmatch(r"(?:19|20)\d{2}(?:\s+(?:19|20)\d{2})*", line)
        ):
            if line not in selected:
                selected.append(line)
        if len(selected) >= 8:
            break
    return "\n".join(selected)


def extract_pages_with_model(
    source: str | Path | bytes,
    pages: list[PageText],
    provider: ModelOCRProvider,
    *,
    dpi: int = 144,
) -> list[PageText]:
    """Render and recognize selected pages sequentially for low-memory machines."""
    extracted: list[PageText] = []
    for page in pages:
        image = render_pdf_page(source, page.number, dpi=dpi)
        recognized = normalize_model_table(provider.extract_page(image))
        header = _context_header(page.text)
        text = "\n".join(part for part in (header, recognized) if part)
        extracted.append(
            PageText(
                number=page.number,
                text=text,
                method=f"ollama:{provider.model}",
                confidence=0.85,
            )
        )
    return extracted

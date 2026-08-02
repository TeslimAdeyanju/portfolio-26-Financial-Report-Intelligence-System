# Document Processing Agent

**Status:** Implemented

Extracts page-level text from PDFs, detects unusable embedded text, and applies targeted
two-pass Tesseract OCR. It also provides a model-agnostic OCR provider interface and a local
GLM-OCR implementation using Ollama's native vision API.

The GLM-OCR path renders only confidently identified financial-statement pages and processes
them sequentially to support memory-constrained Apple silicon machines. Model output is
normalized from HTML or Markdown tables, retains page-level provenance, and is passed through
the same deterministic statement parser and accounting validations as embedded PDF text.

Supported extraction modes are:

- `automatic`: invoke GLM-OCR only when statements are incomplete or validation fails.
- `model_assisted`: invoke GLM-OCR for every identified primary statement page.
- `rules_only`: never contact a model and retain the deterministic/Tesseract pipeline.

All model failures fall back safely to rules-based extraction with a user-visible warning.
Future Excel and PowerPoint readers belong in this folder.

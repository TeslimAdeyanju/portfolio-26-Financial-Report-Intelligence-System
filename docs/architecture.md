# Version 1 architecture

The initial pipeline is deliberately linear and traceable:

```text
PDF upload
  → embedded-text quality check
  → two-pass OCR when required
  → primary statement classification
  → multi-period structured extraction
  → deterministic calculations and validation
  → baseline summary and JSON export
```

- `agents/document_processing_agent/` owns file parsing and page boundaries.
- `agents/metrics_extraction_agent/` extracts supported label/value pairs and records evidence.
- Its `statements.py` builds period-aware income statement, balance sheet, and
  cash flow statement models with currency and scale metadata.
- `agents/data_quality_agent/` reconciles accounting equations and calculated values.
- `agents/narrative_synthesis_agent/` produces a transparent baseline narrative.
- `agents/financial_calculation_engine/` contains deterministic Python formulas; an LLM must
  never calculate ratios.
- `pipeline.py` coordinates the stages and returns a stable domain model.
- `app.py` is a thin Streamlit interface.

## Code organization

```text
backend/fris/
├── agents/
│   ├── document_processing_agent/      # Implemented
│   ├── metrics_extraction_agent/       # Implemented
│   ├── financial_calculation_engine/   # Implemented
│   ├── data_quality_agent/             # Implemented
│   ├── financial_analysis_agent/       # Planned
│   ├── insight_generation_agent/       # Planned
│   ├── risk_assessment_agent/          # Planned
│   ├── visual_blueprint_agent/         # Planned
│   ├── narrative_synthesis_agent/      # Baseline implemented
│   └── export_agent/                    # Planned
├── models.py               # Shared data contracts
└── pipeline.py             # Workflow orchestration
```

Text-based PDFs use their embedded text. Image-only or corrupt-encoding PDFs automatically
fall back to local Tesseract OCR. The OCR path classifies every page at low resolution, then
reruns only primary financial statements at detailed resolution. This reduces processing
time while keeping table values accurate and traceable to their source pages.

Calculations operate on structured period data. ROA, ROE, and asset turnover use average
opening and closing balances when both periods are available. Free cash flow is operating
cash flow plus capital expenditure, where cash outflows are represented as negative values.

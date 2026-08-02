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

- `agents/agent_01_document_processing/` owns file parsing and page boundaries.
- `agents/agent_02_metrics_extraction/` retains every detected label/value row in PDF order and
  records its section and source evidence. Canonical mappings are applied only where a row is
  needed by calculations or validation; unknown labels remain in the structured statement.
- Its `statements.py` builds period-aware income statement, balance sheet, and cash flow
  models with exact display labels, currency, scale, section, and page metadata.
- `agents/agent_04_data_quality/` reconciles accounting equations and calculated values.
- `agents/agent_09_narrative_synthesis/` produces a transparent baseline narrative.
- `agents/agent_03_financial_calculation_engine/` contains deterministic Python formulas; an LLM must
  never calculate ratios.
- `pipeline.py` coordinates the stages and returns a stable domain model.
- `app.py` is a thin Streamlit interface.

## Code organization

```text
backend/fris/
├── agents/
│   ├── agent_01_document_processing/      # Implemented
│   ├── agent_02_metrics_extraction/       # Implemented
│   ├── agent_03_financial_calculation_engine/   # Implemented
│   ├── agent_04_data_quality/             # Implemented
│   ├── agent_05_financial_analysis/       # Planned
│   ├── agent_06_insight_generation/       # Planned
│   ├── agent_07_risk_assessment/          # Planned
│   ├── agent_08_visual_blueprint/         # Planned
│   ├── agent_09_narrative_synthesis/      # Baseline implemented
│   └── agent_10_export/                    # Planned
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

The Data Quality Agent validates balance-sheet totals, accounting equations, gross-profit
reconciliations, current ratios, cash rollforwards, and cash-flow subtotals whenever the
necessary rows are present.

# 📊 CoreInsight Financial Report Intelligence System (FRIS)

> **An AI-powered financial intelligence platform that transforms financial reports into structured metrics, financial insights, risk assessments, and business intelligence using a multi-agent architecture.**

## Overview

The **Financial Report Intelligence System (FRIS)** is an end-to-end financial analysis platform designed to automate the extraction, validation, interpretation, and presentation of information contained in corporate financial reports.

Rather than functioning as a simple chatbot, FRIS operates as an intelligent financial analysis framework. It combines financial domain knowledge, data engineering, artificial intelligence, and software engineering to convert unstructured financial documents into actionable business intelligence.

The platform is being developed as a flagship portfolio project demonstrating modern AI engineering techniques applied to financial analysis.

## Project Vision

Financial analysts spend hours manually reviewing annual reports, calculating financial ratios, identifying risks, preparing management commentary, and building dashboards.

FRIS aims to automate much of this workflow while maintaining transparency, traceability, and professional financial analysis standards.

The long-term objective is to build an extensible financial intelligence platform capable of supporting:

- Financial statement analysis
- Executive reporting
- FP&A workflows
- Investment research
- Board reporting
- Risk assessment
- Business intelligence

## Core Objectives

The system is designed to:

- Extract structured financial information from reports
- Automatically calculate key financial metrics and ratios
- Identify trends and year-on-year movements
- Detect anomalies and financial risks
- Generate evidence-based management commentary
- Produce dashboard specifications for Power BI
- Export structured data for downstream analytics
- Benchmark different open-source language models on financial reasoning tasks

## System Architecture

![CoreInsight FRIS system architecture](docs/assets/workflow-pic.png)

## Multi-Agent Framework

The platform is organised into specialised agents, each responsible for a focused financial task.

| Agent | Responsibility |
| --- | --- |
| Document Processing Agent | Extract text, tables, and financial statements from PDF, Excel, and PowerPoint files |
| Metrics Extraction Agent | Identify and structure financial metrics from reports |
| Financial Calculation Engine | Calculate financial ratios, KPIs, and trends using Python |
| Data Quality Agent | Validate extracted information and detect inconsistencies |
| Financial Analysis Agent | Analyse trends, variances, and business performance |
| Insight Generation Agent | Explain the business meaning behind financial movements |
| Risk Assessment Agent | Identify financial, operational, and reporting risks |
| Visual Blueprint Agent | Generate Power BI dashboard specifications and semantic models |
| Narrative Synthesis Agent | Produce executive summaries and management reports |
| Export Agent | Export results to JSON, CSV, Excel, Power BI-ready tables, PDF, and other destinations |

## Technology Stack

### Backend

- Python

### Artificial Intelligence

- Ollama (local LLM runtime)
- Open-source language models
- Hugging Face models
- MLX (Apple silicon)

### Data Engineering

- Pandas
- NumPy
- PyMuPDF
- OpenPyXL

### Databases

- SQLite
- PostgreSQL
- ChromaDB

### Frontend

- Streamlit

### Business Intelligence

- Power BI

### Version Control

- Git and GitHub

## Model-Agnostic Design

One of the primary design goals is **model independence**. The Financial Intelligence Framework is not tied to any single language model, allowing supported models to be swapped without changing the core business logic.

Supported providers may include:

- Ollama
- Hugging Face
- MLX
- OpenAI
- Anthropic Claude
- Google Gemini
- Future open-source models

This architecture enables multiple language models to be benchmarked using identical financial analysis workflows.

## Planned Features

### Financial Metrics Extraction

- Income statement
- Balance sheet
- Cash flow statement
- Notes to the accounts

### Financial Analysis

- Profitability analysis
- Liquidity analysis
- Solvency analysis
- Efficiency analysis
- Cash flow analysis
- Trend analysis
- Variance analysis

### Automated Calculations

- Gross margin
- Operating margin
- Net margin
- EBITDA margin
- Current ratio
- Quick ratio
- Debt-to-equity ratio
- Return on assets (ROA)
- Return on equity (ROE)
- Interest coverage
- Asset turnover
- Free cash flow
- Earnings per share (EPS)
- Working capital

### AI-Generated Insights

- Executive summaries
- Management commentary
- Financial highlights
- Risk commentary
- Business drivers
- Investment considerations

### Export Formats

- JSON
- CSV
- Excel
- PDF
- Markdown
- Power BI-ready tables

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r development/requirements.txt
streamlit run app.py
```

Run the automated checks with `pytest`. Version 1 currently supports text-based PDFs;
corrupt or image-only PDFs automatically use local Tesseract OCR. Install the OCR runtime
with `brew install tesseract` on macOS or through your operating system's package manager.

## Version 1 Capabilities

- Reporting-period extraction for multi-column statements
- Currency and unit-scale recognition (units, thousands, millions, and billions)
- Structured income statement, balance sheet, and cash flow statement rows
- Page-level evidence for every extracted row
- Two-pass OCR: low-resolution page classification followed by detailed statement OCR
- Accounting equation, gross-profit, and current-ratio validation
- Multi-period margins, liquidity, debt, efficiency, return, cash flow, and EPS metrics
- JSON export of statements, calculations, validations, evidence, and warnings

## Milestone: Phase 1 Complete

Phase 1 was completed and validated against the included 80-page Apple 2022 Form 10-K.
The production pipeline automatically detected corrupt embedded PDF text, classified the
document at low resolution, and applied detailed OCR only to the primary statements.

### Verified extraction

| Statement | Source page | Reporting periods | Currency and unit |
| --- | ---: | --- | --- |
| Consolidated statements of operations | 32 | 2022, 2021, 2020 | USD millions |
| Consolidated balance sheets | 34 | 2022, 2021 | USD millions |
| Consolidated statements of cash flows | 36 | 2022, 2021, 2020 | USD millions |

### Verified 2022 calculations

| KPI | Result |
| --- | ---: |
| Gross margin | 43.31% |
| Operating margin | 30.29% |
| Net margin | 25.31% |
| Current ratio | 0.88x |
| Working capital | $(18,577) million |
| Debt-to-equity | 2.37x |
| Debt ratio | 0.34x |
| Asset turnover | 1.12x |
| Return on average assets | 28.36% |
| Return on average equity | 175.46% |
| Free cash flow | $111,443 million |
| Basic / diluted EPS | $6.15 / $6.11 |

All seven available accounting-equation, gross-profit, and current-ratio validation checks
passed. The complete automated suite contains nine passing tests. Full two-pass OCR and
analysis of the sample report completes in approximately 50 seconds on the development
machine.

### Agent implementation status

| Agent | Status |
| --- | --- |
| Document Processing Agent | Implemented |
| Metrics Extraction Agent | Implemented |
| Financial Calculation Engine | Implemented |
| Data Quality Agent | Implemented |
| Financial Analysis Agent | Planned folder ready |
| Insight Generation Agent | Planned folder ready |
| Risk Assessment Agent | Planned folder ready |
| Visual Blueprint Agent | Planned folder ready |
| Narrative Synthesis Agent | Baseline implemented |
| Export Agent | JSON available; additional formats planned |

## Roadmap

### Version 1

- PDF upload ✅
- Multi-period structured statement extraction ✅
- Financial ratio and KPI calculation ✅
- Financial equation validation ✅
- Targeted OCR fallback ✅
- Executive summary ✅
- JSON export ✅

### Version 2

- Multi-agent workflow
- Risk detection
- Dashboard blueprint generation
- Power BI export
- Financial data validation

### Version 3

- Multi-year trend analysis
- Peer comparison
- Company benchmarking
- Investment scoring
- Stock valuation models
- Model benchmarking framework

### Version 4

- Live financial data integration
- Portfolio analysis
- Intelligent research reports
- Financial knowledge graph
- Personal AI financial research assistant

## Repository Structure

```text
financial-report-intelligence-system/
├── backend/fris/                  # Application package
│   ├── agents/                    # One folder per agent responsibility
│   │   ├── document_processing_agent/
│   │   ├── metrics_extraction_agent/
│   │   ├── financial_calculation_engine/
│   │   ├── data_quality_agent/
│   │   ├── financial_analysis_agent/
│   │   ├── insight_generation_agent/
│   │   ├── risk_assessment_agent/
│   │   ├── visual_blueprint_agent/
│   │   ├── narrative_synthesis_agent/
│   │   └── export_agent/
│   ├── models.py
│   └── pipeline.py
├── development/
│   ├── tests/                     # Automated tests
│   ├── tools/                     # Developer and maintenance tools
│   └── requirements.txt           # Development dependencies
├── docs/
│   ├── assets/
│   └── architecture.md
├── sample_reports/                # Local reports used for evaluation
├── app.py                         # Streamlit entry point
├── pyproject.toml                 # Python package configuration
├── requirements.txt               # Runtime installation
└── README.md
```

Development-only tests, dependencies, and tools are consolidated under `development/`.
Every responsibility in the Multi-Agent Framework has its own folder under
`backend/fris/agents/`, including documented placeholders for planned agents. See each
folder's `README.md` and `docs/architecture.md` for its status and extension boundary.

## Guiding Principles

- Financial accuracy before AI creativity
- Python performs deterministic calculations
- AI provides interpretation and reasoning
- Every insight should be traceable to source evidence
- Modular architecture with interchangeable models
- Transparent and explainable financial intelligence

## Disclaimer

This project is intended for financial analysis, research, education, and decision support. It does not provide financial advice or investment recommendations. Users remain responsible for validating outputs and making their own financial decisions.

## Author

**Teslim Adeyanju, ACA**<br>
Financial Data Analyst | Chartered Accountant | AI & Financial Intelligence Engineer

Building practical AI systems that combine finance, data engineering, and machine learning to solve real-world business problems.

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

```text
                     Financial Report
                             │
                             ▼
                  Document Processing Layer
                             │
                             ▼
                Financial Intelligence Engine
                             │
      ┌──────────┬──────────┬──────────┬──────────┐
      ▼          ▼          ▼          ▼
   Metrics    Analysis     Risk      Insights
                             │
                             ▼
                Financial Calculation Engine
                             │
                             ▼
                  Narrative Generator
                             │
                             ▼
                       Export Layer
```

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

## Roadmap

### Version 1

- PDF upload
- Metrics extraction
- Financial ratio calculation
- Executive summary
- JSON export

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

## Proposed Repository Structure

```text
financial-report-intelligence-system/
├── docs/
├── backend/
├── frontend/
├── agents/
├── models/
├── prompts/
├── financial_engine/
├── exports/
├── evaluation/
├── tests/
├── sample_reports/
├── app.py
├── requirements.txt
└── README.md
```

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

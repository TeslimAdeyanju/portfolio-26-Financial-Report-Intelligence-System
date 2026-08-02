"""Streamlit entry point for CoreInsight FRIS Version 1."""

from __future__ import annotations

import json

import streamlit as st

from fris import ExtractionMode, FinancialReportPipeline


def format_financial_value(value: float) -> str:
    """Format statement amounts for display without changing stored numeric data."""
    absolute = abs(value)
    formatted = f"{absolute:,.0f}" if value == int(value) else f"{absolute:,.2f}"
    return f"({formatted})" if value < 0 else formatted


def format_ratio_value(name: str, value: float) -> str:
    if name in {"working_capital", "free_cash_flow"}:
        return format_financial_value(value)
    if name in {
        "gross_margin",
        "operating_margin",
        "net_margin",
        "return_on_assets",
        "return_on_equity",
    }:
        return f"{value:,.2f}%"
    if name in {"basic_eps", "diluted_eps"}:
        return f"{value:,.2f}"
    return f"{value:,.2f}x"


def format_movement_value(item: dict, value: float) -> str:
    if item["metric_type"] == "fact" or item["unit"] == "amount":
        return format_financial_value(value)
    if item["unit"] == "percentage_points":
        return f"{value:,.2f}%"
    return f"{value:,.2f}x"


def format_movement_change(item: dict) -> str:
    value = item["absolute_change"]
    sign = "+" if value > 0 else ""
    if item["metric_type"] == "fact" or item["unit"] == "amount":
        return f"{sign}{format_financial_value(value)}"
    if item["unit"] == "percentage_points":
        return f"{sign}{value:,.2f} pp"
    return f"{sign}{value:,.2f}x"


def format_risk_value(item: dict) -> str:
    value = item["observed_value"]
    if item["unit"] in {"percentage", "percentage_points"}:
        suffix = "%" if item["unit"] == "percentage" else " pp"
        return f"{value:+,.2f}{suffix}"
    if item["unit"] == "ratio":
        return f"{value:,.2f}x"
    return format_financial_value(value)


st.set_page_config(page_title="CoreInsight FRIS", page_icon="📊", layout="wide")
st.title("CoreInsight Financial Report Intelligence")
st.caption("Upload a financial PDF to extract structured, traceable statements and ratios.")

mode_labels = {
    "Automatic — use GLM-OCR only when rules are incomplete": ExtractionMode.AUTOMATIC.value,
    "Model-assisted — run GLM-OCR on statement pages": ExtractionMode.MODEL_ASSISTED.value,
    "Rules only — do not call a model": ExtractionMode.RULES_ONLY.value,
}
selected_mode_label = st.selectbox("Extraction mode", tuple(mode_labels))
selected_mode = mode_labels[selected_mode_label]

with st.expander("Local model settings"):
    ollama_url = st.text_input("Ollama URL", value="http://127.0.0.1:11434")
    model_name = st.text_input("Vision model", value="glm-ocr:latest")
    if st.button("Check model connection"):
        status = FinancialReportPipeline(
            extraction_mode=selected_mode,
            ollama_url=ollama_url,
            model_name=model_name,
        ).model_status()
        (st.success if status.available else st.error)(status.detail)

uploaded = st.file_uploader("Financial report", type=["pdf"])
if uploaded and st.button("Analyse report", type="primary"):
    try:
        with st.spinner("Analysing report…"):
            result = FinancialReportPipeline(
                extraction_mode=selected_mode,
                ollama_url=ollama_url,
                model_name=model_name,
            ).analyze(uploaded.getvalue(), uploaded.name)
        payload = result.to_dict()
        st.session_state["analysis"] = payload
    except Exception as exc:
        st.error(f"The report could not be analysed: {exc}")

if payload := st.session_state.get("analysis"):
    model_label = payload.get("model_used") or "not used"
    st.caption(
        f"Extraction mode: {payload.get('extraction_mode', 'rules_only')} · "
        f"Model: {model_label}"
    )
    for warning in payload["warnings"]:
        st.warning(warning)

    st.subheader("Executive summary")
    for statement in payload["summary"]:
        st.write(f"• {statement}")

    fact_tab, analysis_tab, risk_tab, statement_tab, ratio_tab, validation_tab, evidence_tab = st.tabs(
        [
            "Key Financial Facts",
            "Analysis",
            "Risks",
            "Full Statements",
            "Ratios",
            "Validation",
            "Evidence",
        ]
    )
    with fact_tab:
        facts = payload.get("financial_facts", {})
        reported = {name: fact for name, fact in facts.items() if fact["status"] == "reported"}
        missing = {name: fact for name, fact in facts.items() if fact["status"] != "reported"}
        st.metric("Facts available", f"{len(reported)}/{len(facts)}")
        periods = sorted(
            {period for fact in reported.values() for period in fact["values"]},
            key=lambda value: int(value) if value.isdigit() else value,
            reverse=True,
        )
        st.dataframe(
            [
                {
                    "category": fact["category"],
                    "metric": name.replace("_", " ").title(),
                    "source label": fact["source_label"],
                    **{
                        period: (
                            format_financial_value(fact["values"][period])
                            if period in fact["values"]
                            else ""
                        )
                        for period in periods
                    },
                    "currency / unit": f"{fact['currency']} {fact['unit']}",
                    "page": fact["evidence"]["page"] if fact.get("evidence") else "",
                    "method": fact["extraction_method"],
                    "confidence": f"{fact['confidence']:.0%}",
                }
                for name, fact in reported.items()
            ],
            width="stretch",
            hide_index=True,
        )
        with st.expander(f"Unavailable or non-separately-reported facts ({len(missing)})"):
            st.dataframe(
                [
                    {
                        "category": fact["category"],
                        "metric": name.replace("_", " ").title(),
                        "reason": fact["reason"],
                    }
                    for name, fact in missing.items()
                ],
                width="stretch",
                hide_index=True,
            )
    with analysis_tab:
        movements = payload.get("financial_movements", [])
        if not movements:
            st.info("At least two comparable reporting periods are required for trend analysis.")
        else:
            favorable = sum(item["assessment"] == "favorable" for item in movements)
            adverse = sum(item["assessment"] == "adverse" for item in movements)
            contextual = sum(item["assessment"] == "contextual" for item in movements)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Movements analysed", len(movements))
            col2.metric("Favorable", favorable)
            col3.metric("Adverse", adverse)
            col4.metric("Contextual", contextual)
            st.dataframe(
                [
                    {
                        "category": item["category"],
                        "metric": item["name"].replace("_", " ").title(),
                        "comparison": f"{item['current_period']} vs {item['prior_period']}",
                        "current": format_movement_value(item, item["current_value"]),
                        "prior": format_movement_value(item, item["prior_value"]),
                        "change": format_movement_change(item),
                        "% change": (
                            f"{item['percentage_change']:+,.2f}%"
                            if item["percentage_change"] is not None
                            else "n/m"
                        ),
                        "direction": item["direction"],
                        "assessment": item["assessment"],
                        "rationale": item["rationale"],
                        "page": item["evidence"]["page"] if item.get("evidence") else "",
                    }
                    for item in movements
                ],
                width="stretch",
                hide_index=True,
            )
    with risk_tab:
        risks = payload.get("risk_findings", [])
        if not risks:
            st.success("No risks crossed the configured thresholds for the available facts.")
        else:
            high = sum(item["severity"] == "high" for item in risks)
            medium = sum(item["severity"] == "medium" for item in risks)
            low = sum(item["severity"] == "low" for item in risks)
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Risk findings", len(risks))
            col2.metric("High", high)
            col3.metric("Medium", medium)
            col4.metric("Low", low)
            st.dataframe(
                [
                    {
                        "severity": item["severity"].upper(),
                        "category": item["category"],
                        "risk": item["title"],
                        "period": item["period"],
                        "observed": format_risk_value(item),
                        "trigger": item["trigger"],
                        "implication": item["implication"],
                        "suggested action": item["suggested_action"],
                        "page": item["evidence"]["page"] if item.get("evidence") else "",
                    }
                    for item in risks
                ],
                width="stretch",
                hide_index=True,
            )
    with statement_tab:
        if not payload.get("statements"):
            st.info("No structured statements were extracted.")
        for statement_name, statement in payload.get("statements", {}).items():
            st.markdown(
                f"**{statement_name.replace('_', ' ').title()}** — "
                f"{statement['currency']} in {statement['unit']} · "
                f"page {statement['page']} · {len(statement['rows'])} rows · "
                f"{statement.get('extraction_method', 'deterministic')}"
            )
            st.dataframe(
                [
                    {
                        "section": row.get("section") or "",
                        "row": row.get("label") or row_name,
                        **{
                            period: format_financial_value(value)
                            for period, value in row["values"].items()
                        },
                    }
                    for row_name, row in statement["rows"].items()
                ],
                width="stretch",
                hide_index=True,
                height=min(1_000, 38 * (len(statement["rows"]) + 1)),
            )
    with ratio_tab:
        ratio_rows = []
        for period, ratios in payload.get("period_ratios", {}).items():
            for ratio_name, item in ratios.items():
                ratio_rows.append(
                    {
                        "period": period,
                        "metric": ratio_name,
                        "value": format_ratio_value(ratio_name, item["value"]),
                        "formula": item["formula"],
                    }
                )
        st.dataframe(ratio_rows, width="stretch", hide_index=True)
    with validation_tab:
        validations = payload.get("validations", [])
        if validations:
            passed = sum(item["passed"] for item in validations)
            st.metric("Checks passed", f"{passed}/{len(validations)}")
            st.dataframe(validations, width="stretch", hide_index=True)
        else:
            st.info("No financial validation checks could be completed.")
    with evidence_tab:
        st.json(
            {
                statement_name: {
                    row_name: {
                        "evidence": row["evidence"],
                        "extraction_method": row.get("extraction_method", "deterministic"),
                        "confidence": row.get("confidence", 1.0),
                    }
                    for row_name, row in statement["rows"].items()
                }
                for statement_name, statement in payload.get("statements", {}).items()
            }
        )

    st.download_button(
        "Download JSON",
        data=json.dumps(payload, indent=2),
        file_name="financial-analysis.json",
        mime="application/json",
    )

st.divider()
st.caption("For research and decision support only. Validate all outputs against source reports.")

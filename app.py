"""Streamlit entry point for CoreInsight FRIS Version 1."""

from __future__ import annotations

import json

import streamlit as st

from fris import FinancialReportPipeline


st.set_page_config(page_title="CoreInsight FRIS", page_icon="📊", layout="wide")
st.title("CoreInsight Financial Report Intelligence")
st.caption("Upload a financial PDF to extract structured, traceable statements and ratios.")

uploaded = st.file_uploader("Financial report", type=["pdf"])
if uploaded and st.button("Analyse report", type="primary"):
    try:
        with st.spinner("Analysing report…"):
            result = FinancialReportPipeline().analyze(uploaded.getvalue(), uploaded.name)
        payload = result.to_dict()
        st.session_state["analysis"] = payload
    except Exception as exc:
        st.error(f"The report could not be analysed: {exc}")

if payload := st.session_state.get("analysis"):
    for warning in payload["warnings"]:
        st.warning(warning)

    st.subheader("Executive summary")
    for statement in payload["summary"]:
        st.write(f"• {statement}")

    statement_tab, ratio_tab, validation_tab, evidence_tab = st.tabs(
        ["Statements", "Ratios", "Validation", "Evidence"]
    )
    with statement_tab:
        if not payload.get("statements"):
            st.info("No structured statements were extracted.")
        for statement_name, statement in payload.get("statements", {}).items():
            st.markdown(
                f"**{statement_name.replace('_', ' ').title()}** — "
                f"{statement['currency']} in {statement['unit']} (page {statement['page']})"
            )
            st.dataframe(
                [
                    {"row": row_name, **row["values"]}
                    for row_name, row in statement["rows"].items()
                ],
                use_container_width=True,
            )
    with ratio_tab:
        ratio_rows = []
        for period, ratios in payload.get("period_ratios", {}).items():
            for ratio_name, item in ratios.items():
                ratio_rows.append(
                    {
                        "period": period,
                        "metric": ratio_name,
                        "value": item["value"],
                        "formula": item["formula"],
                    }
                )
        st.dataframe(ratio_rows, use_container_width=True)
    with validation_tab:
        validations = payload.get("validations", [])
        if validations:
            passed = sum(item["passed"] for item in validations)
            st.metric("Checks passed", f"{passed}/{len(validations)}")
            st.dataframe(validations, use_container_width=True)
        else:
            st.info("No financial validation checks could be completed.")
    with evidence_tab:
        st.json(
            {
                statement_name: {
                    row_name: row["evidence"]
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

from fris.agents.agent_01_document_processing import PageText
from fris.agents.agent_02_metrics_extraction import (
    FACT_DEFINITIONS,
    extract_financial_facts,
    extract_statements,
)


def test_builds_stable_fact_pack_with_source_labels_and_missing_reasons() -> None:
    statements = extract_statements(
        [
            PageText(
                4,
                "CONSOLIDATED STATEMENTS OF INCOME\n"
                "(USD in millions)\n2025 2024\n"
                "Net sales 1,000 900\n"
                "Operating income 200 180\n"
                "Income before provision for income taxes 180 160\n"
                "Provision for income taxes 40 35\n"
                "Net income 140 125",
            )
        ]
    )

    facts = extract_financial_facts(statements)

    assert len(facts) == len(FACT_DEFINITIONS)
    assert facts["revenue"].values == {"2025": 1_000, "2024": 900}
    assert facts["revenue"].source_label == "Net sales"
    assert facts["revenue"].evidence.page == 4
    assert facts["total_assets"].status == "not_found"
    assert "balance sheet was not identified" in facts["total_assets"].reason
    assert facts["gross_profit"].status == "not_found"
    assert facts["gross_profit"].values == {}

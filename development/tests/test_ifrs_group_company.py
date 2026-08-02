import fitz

from fris import ExtractionMode, FinancialReportPipeline
from fris.agents.agent_01_document_processing import PageText, is_primary_statement
from fris.agents.agent_02_metrics_extraction import (
    extract_financial_facts,
    extract_statements,
)


def test_recognizes_ifrs_statement_titles_and_rejects_auditor_references() -> None:
    assert is_primary_statement("EE Limited\n16\nGroup income statement\n2015\n2014")
    assert is_primary_statement(
        "EE Limited\n18\nStatements of financial position\n2015\n2014"
    )
    assert is_primary_statement("EE Limited\n22\nStatements of cash flows\n2015\n2014")
    assert not is_primary_statement(
        "Independent auditor's report\nWe audited the Group income statement and "
        "Statements of financial position"
    )


def test_extracts_group_values_not_notes_or_company_columns() -> None:
    pages = [
        PageText(
            16,
            "Group income statement\nFor the year ended 31 December 2015\n"
            "2015)\n2014)\nNotes\n£m)\n£m)\n"
            "Revenue\n7\n6,311)\n6,327)\n"
            "Group operating profit/(loss)\n507)\n(152)\n"
            "Profit/(loss) before tax\n416)\n(255)\n"
            "Income tax\n16\n(84)\n38)\n"
            "Profit/(loss) for the year attributable to the equity holders of the parent\n"
            "332)\n(217)",
        ),
        PageText(
            18,
            "Statements of financial position\nGroup\nCompany\n"
            "2015)\n2014)\n2015)\n2014)\nNotes\n£m)\n£m)\n£m)\n£m)\n"
            "Cash and cash equivalents\n22\n394)\n411)\n388)\n405)\n"
            "Total current assets\n1,439)\n1,482)\n3,000)\n3,100)\n"
            "Total assets\n13,162)\n13,859)\n6,000)\n6,100)\n"
            "Total current liabilities\n(2,577)\n(2,444)\n(2,000)\n(2,100)\n"
            "Total liabilities\n(4,510)\n(4,938)\n(4,000)\n(4,100)\n"
            "Total net assets\n8,652)\n8,921)\n2,000)\n2,000)",
        ),
        PageText(
            22,
            "Statements of cash flows\nGroup\nCompany\n"
            "2015)\n2014)\n2015)\n2014)\nNotes\n£m)\n£m)\n£m)\n£m)\n"
            "Net cash provided by operating activities\n1,272)\n1,188)\n900)\n800)\n"
            "Purchases of property, plant and equipment\nand intangible assets\n"
            "17, 18\n(594)\n(596)\n(400)\n(410)",
        ),
        PageText(
            23,
            "Statements of cash flows (continued)\nGroup\nCompany\n"
            "2015)\n2014)\n2015)\n2014)\nNotes\n£m)\n£m)\n£m)\n£m)\n"
            "Net cash used in financing activities\n(694)\n(592)\n(600)\n(500)\n"
            "Cash and cash equivalents at the end of the year\n394)\n411)\n388)\n405)",
        ),
    ]

    statements = extract_statements(pages)
    facts = extract_financial_facts(statements)

    assert facts["revenue"].values == {"2015": 6_311, "2014": 6_327}
    assert facts["cash_and_equivalents"].values == {"2015": 394, "2014": 411}
    assert facts["current_liabilities"].values == {"2015": 2_577, "2014": 2_444}
    assert facts["total_equity"].values == {"2015": 8_652, "2014": 8_921}
    assert facts["operating_cash_flow"].values == {"2015": 1_272, "2014": 1_188}
    assert facts["capital_expenditure"].values == {"2015": -594, "2014": -596}
    assert facts["ending_cash"].values == {"2015": 394, "2014": 411}


def test_pipeline_does_not_treat_narrative_number_as_revenue() -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Revenue recognition note\nDiscount rate 7.00")
    payload = document.tobytes()
    document.close()

    result = FinancialReportPipeline(extraction_mode=ExtractionMode.RULES_ONLY).analyze(payload)

    assert not result.metrics
    assert result.financial_facts["revenue"].status == "not_found"
    assert all("7.00" not in line for line in result.summary)

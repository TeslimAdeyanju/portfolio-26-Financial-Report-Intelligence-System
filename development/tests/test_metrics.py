from fris.agents.document_processing_agent import PageText, text_quality_issue
from fris.agents.metrics_extraction_agent import extract_metrics, select_primary_statement_pages


def test_extracts_metrics_with_page_evidence() -> None:
    metrics = extract_metrics(
        [PageText(1, "Revenue 1,250.5\nGross profit 500\nNet income (75)")]
    )

    assert metrics["revenue"].value == 1250.5
    assert metrics["gross_profit"].value == 500
    assert metrics["net_income"].value == -75
    assert metrics["revenue"].evidence is not None
    assert metrics["revenue"].evidence.page == 1


def test_detects_corrupt_embedded_pdf_text() -> None:
    pages = [PageText(1, "Revenue\x01100\x01Gross profit\x0140")]

    assert text_quality_issue(pages) == (
        "The PDF's embedded text encoding is corrupt and requires OCR."
    )


def test_extracts_ocr_table_values_from_following_lines() -> None:
    pages = [
        PageText(
            32,
            "CONSOLIDATED STATEMENTS OF OPERATIONS\n"
            "Total net sales\n394,328\n365,817\n"
            "Gross margin\n170,782\n152,836\n"
            "Net income\n$\n99,803\n$\n94,680",
        )
    ]

    metrics = extract_metrics(select_primary_statement_pages(pages))

    assert metrics["revenue"].value == 394_328
    assert metrics["gross_profit"].value == 170_782
    assert metrics["net_income"].value == 99_803


def test_uses_total_current_assets_not_section_header() -> None:
    pages = [
        PageText(
            34,
            "CONSOLIDATED BALANCE SHEETS\n"
            "Current assets:\nCash and cash equivalents\n23,646\n"
            "Total current assets\n135,405\n"
            "Current liabilities:\nAccounts payable\n64,115\n"
            "Total current liabilities\n153,982",
        )
    ]

    metrics = extract_metrics(select_primary_statement_pages(pages))

    assert metrics["current_assets"].value == 135_405
    assert metrics["current_liabilities"].value == 153_982

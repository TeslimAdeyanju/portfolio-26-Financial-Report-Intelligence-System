from pathlib import Path

from fris import FinancialReportPipeline


SAMPLES = Path("sample_reports")


def test_amazon_complete_primary_statements() -> None:
    result = FinancialReportPipeline().analyze(SAMPLES / "Amazon-2025-Annual-Report.pdf")

    assert len(result.statements["income_statement"].rows) >= 23
    assert len(result.statements["balance_sheet"].rows) >= 26
    assert len(result.statements["cash_flow_statement"].rows) >= 29
    assert result.statements["income_statement"].rows["revenue"].values["2025"] == 716_924
    assert result.statements["balance_sheet"].rows["cash_and_equivalents"].values["2025"] == 86_810
    assert result.statements["cash_flow_statement"].rows["operating_cash_flow"].values["2025"] == 139_514
    assert result.period_ratios["2025"]["free_cash_flow"].value == 7_695
    assert result.financial_facts["revenue"].values["2025"] == 716_924
    assert result.financial_facts["total_assets"].status == "reported"


def test_colgate_complete_primary_statements() -> None:
    result = FinancialReportPipeline().analyze(SAMPLES / "Colgate_statement.pdf")

    assert len(result.statements["income_statement"].rows) >= 17
    assert len(result.statements["balance_sheet"].rows) >= 31
    assert len(result.statements["cash_flow_statement"].rows) >= 33
    assert result.statements["income_statement"].rows["revenue"].values["2025"] == 20_382
    assert result.statements["balance_sheet"].rows["total_equity"].values["2025"] == 365
    assert result.statements["cash_flow_statement"].rows["ending_cash"].values["2025"] == 1_288
    assert result.period_ratios["2025"]["free_cash_flow"].value == 3_634
    assert all(validation.passed for validation in result.validations)
    assert result.financial_facts["revenue"].source_label == "Net sales"
    assert result.financial_facts["operating_cash_flow"].values["2025"] == 4_198

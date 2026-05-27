import os
from pathlib import Path

import pytest
from boomerang_score.core.models import Competition, Participant
from boomerang_score.core.constants import (
    DISC_CODE_ACC, DISC_CODE_AUS, DISC_CODE_MTA,
    DISC_CODE_FC, DISC_CODE_TC, DISC_CODE_END,
    DISC_LABEL_ACC, DISC_LABEL_AUS, DISC_LABEL_MTA,
    DISC_LABEL_FC, DISC_LABEL_TC, DISC_LABEL_END,
)
from boomerang_score.services.individual_pdf_exporter import IndividualPdfExporter


def _generate_sample_report_pdf(test_data_path: Path, logo_filename: str, output_filename: str):
    # 1. Setup mock data
    competition = Competition(title="Test Boomerang Championship 2026")

    disciplines = {
        DISC_CODE_ACC: type('MockDisc', (), {'label': DISC_LABEL_ACC}),
        DISC_CODE_AUS: type('MockDisc', (), {'label': DISC_LABEL_AUS}),
        DISC_CODE_MTA: type('MockDisc', (), {'label': DISC_LABEL_MTA}),
        DISC_CODE_FC: type('MockDisc', (), {'label': DISC_LABEL_FC}),
        DISC_CODE_TC: type('MockDisc', (), {'label': DISC_LABEL_TC}),
        DISC_CODE_END: type('MockDisc', (), {'label': DISC_LABEL_END}),
    }

    # Mark disciplines as active in competition
    competition.set_active_disciplines({DISC_CODE_ACC, DISC_CODE_AUS, DISC_CODE_MTA, DISC_CODE_FC, DISC_CODE_TC, DISC_CODE_END})

    # Add a participant
    p = Participant(name="John", startnumber=42)
    p.set_result(DISC_CODE_ACC, 42)
    p.set_points(DISC_CODE_ACC, 111)
    p.set_rank(DISC_CODE_ACC, 1)

    p.set_result(DISC_CODE_AUS, 42)
    p.set_points(DISC_CODE_AUS, 111)
    p.set_rank(DISC_CODE_AUS, 1)

    p.set_result(DISC_CODE_MTA, 42)
    p.set_points(DISC_CODE_MTA, 111)
    p.set_rank(DISC_CODE_MTA, 5)

    p.set_result(DISC_CODE_FC, 42)
    p.set_points(DISC_CODE_FC, 111)
    p.set_rank(DISC_CODE_FC, 2)

    p.set_result(DISC_CODE_TC, 42)
    p.set_points(DISC_CODE_TC, 111)
    p.set_rank(DISC_CODE_TC, 3)

    p.set_result(DISC_CODE_END, 42)
    p.set_points(DISC_CODE_END, 111)
    p.set_rank(DISC_CODE_END, 4)

    p.total_points = 247.5
    p.overall_rank = 3

    competition.add_participant(p)

    # 2. Export to PDF
    logo_path = test_data_path / logo_filename
    exporter = IndividualPdfExporter(competition, disciplines)
    output_filepath = test_data_path / output_filename

    print(f"Generating PDF report: {output_filepath}...")
    exporter.export(str(output_filepath), [str(p.startnumber)], logo_path=str(logo_path))

    print(f"Successfully generated report at: {output_filepath}")
    print("You can now open this file to visually check the rendering.")

    assert os.path.exists(output_filepath)


@pytest.mark.manual
def test_generate_sample_report_pdf_for_manual_inspection_with_round_logo_6_events(test_data_path: Path):
    _generate_sample_report_pdf(test_data_path, "round_logo.png", "sample_participant_report.pdf")


@pytest.mark.manual
def test_generate_sample_report_pdf_for_manual_inspection_with_vertical_logo_6_events(test_data_path: Path):
    _generate_sample_report_pdf(test_data_path, "vertical_logo.png", "sample_participant_report_vertical_logo.pdf")


@pytest.mark.manual
def test_generate_sample_report_pdf_for_manual_inspection_with_horizontal_logo_6_events(test_data_path: Path):
    _generate_sample_report_pdf(test_data_path, "horizontal_logo.png", "sample_participant_report_horizontal_logo.pdf")


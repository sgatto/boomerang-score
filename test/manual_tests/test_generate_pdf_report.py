import os
from pathlib import Path

import pytest
from boomerang_score.core.models import Competition, Participant
from boomerang_score.core.constants import (
    DISC_CODE_ACC, DISC_CODE_AUS, DISC_CODE_MTA,
    DISC_LABEL_ACC, DISC_LABEL_AUS, DISC_LABEL_MTA
)
from boomerang_score.services.individual_pdf_exporter import IndividualPdfExporter

@pytest.mark.manual
def test_generate_sample_report(test_data_path: Path):
    # 1. Setup mock data
    competition = Competition(title="Test Boomerang Championship 2026")
    
    disciplines = {
        DISC_CODE_ACC: type('MockDisc', (), {'label': DISC_LABEL_ACC}),
        DISC_CODE_AUS: type('MockDisc', (), {'label': DISC_LABEL_AUS}),
        DISC_CODE_MTA: type('MockDisc', (), {'label': DISC_LABEL_MTA}),
    }
    
    # Mark disciplines as active in competition
    competition.set_active_disciplines({DISC_CODE_ACC, DISC_CODE_AUS, DISC_CODE_MTA})
    
    # Add a participant
    p = Participant(name="John", startnumber=42)
    p.set_result(DISC_CODE_ACC, 45.0)
    p.set_points(DISC_CODE_ACC, 85.5)
    p.set_rank(DISC_CODE_ACC, 2)
    
    p.set_result(DISC_CODE_AUS, 23.5)
    p.set_points(DISC_CODE_AUS, 92.0)
    p.set_rank(DISC_CODE_AUS, 1)
    
    p.set_result(DISC_CODE_MTA, 35.2)
    p.set_points(DISC_CODE_MTA, 70.0)
    p.set_rank(DISC_CODE_MTA, 5)
    
    p.total_points = 247.5
    p.overall_rank = 3
    
    competition.add_participant(p)
    # logo path
    logo_path = test_data_path / "logo.png"
    # 2. Export to PDF
    exporter = IndividualPdfExporter(competition, disciplines)
    output_filepath = test_data_path / "sample_participant_report.pdf"
    
    print(f"Generating PDF report: {output_filepath}...")
    exporter.export(str(output_filepath), [str(p.startnumber)], logo_path=str(logo_path))
    
    print(f"Successfully generated report at: {output_filepath}")
    print("You can now open this file to visually check the rendering.")
    
    assert os.path.exists(output_filepath)


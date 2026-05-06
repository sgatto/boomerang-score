import os
import unittest
import csv
from boomerang_score.core.models import Competition, Participant
from boomerang_score.services.export_service import ExportService
from boomerang_score.services.individual_pdf_exporter import IndividualPdfExporter
from boomerang_score.services.participant_report_page import ParticipantReportPage


class TestExportService(unittest.TestCase):
    def setUp(self):
        self.competition = Competition(title="Test Competition")
        self.p1 = Participant(name="John Doe", startnumber=1)
        self.p1.total_points = 100.0
        self.p1.overall_rank = 1
        self.p1.set_result("acc", 15.0)
        self.p1.set_points("acc", 50.0)
        self.p1.set_rank("acc", 1)
        self.competition.add_participant(self.p1)

        self.p2 = Participant(name="Jane Smith", startnumber=2)
        self.p2.total_points = 80.0
        self.p2.overall_rank = 2
        self.competition.add_participant(self.p2)

        # Mock disciplines list
        class MockDisc:
            def __init__(self, code, label):
                self.code = code
                self.label = label

        self.disciplines = [MockDisc("acc", "Accuracy")]
        self.export_service = ExportService(self.competition, self.disciplines)
        self.test_csv = "test_export_full.csv"

    def tearDown(self):
        if os.path.exists(self.test_csv):
            os.remove(self.test_csv)

    def test_export_csv_default(self):
        self.export_service.export_csv(self.test_csv)
        self.assertTrue(os.path.exists(self.test_csv))

        with open(self.test_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            rows = list(reader)

        self.assertEqual(len(rows), 3)  # Header + 2 participants
        self.assertEqual(rows[0], ["name", "startnumber", "total", "overall_rank"])
        self.assertEqual(rows[1], ["John Doe", "1", "100", "1"])
        self.assertEqual(rows[2], ["Jane Smith", "2", "80", "2"])

    def test_export_csv_with_disciplines(self):
        visible_columns = ["name", "acc_res", "acc_pts", "acc_rank"]
        column_headers = {
            "name": "Name",
            "acc_res": "Acc Result",
            "acc_pts": "Acc Points",
            "acc_rank": "Acc Rank",
        }
        self.export_service.export_csv(self.test_csv, visible_columns, column_headers)

        with open(self.test_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            rows = list(reader)

        self.assertEqual(rows[0], ["Name", "Acc Result", "Acc Points", "Acc Rank"])
        self.assertEqual(rows[1], ["John Doe", "15", "50", "1"])
        self.assertEqual(rows[2], ["Jane Smith", "", "", ""])

    def test_export_csv_include_header(self):
        self.export_service.export_csv(self.test_csv, include_header=True)

        with open(self.test_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            rows = list(reader)

        self.assertEqual(rows[0][0], "Titel")
        self.assertEqual(rows[0][1], "Test Competition")
        self.assertEqual(rows[1][0], "Datum")
        self.assertEqual(rows[3], ["name", "startnumber", "total", "overall_rank"])

    def test_load_csv(self):
        # Create a CSV to load
        self.export_service.export_csv(self.test_csv, include_header=True)

        data = self.export_service.load_csv(self.test_csv)
        self.assertEqual(data["title"], "Test Competition")
        self.assertEqual(len(data["participants"]), 2)
        self.assertEqual(data["participants"][0]["name"], "John Doe")
        self.assertEqual(data["participants"][1]["name"], "Jane Smith")

    def test_export_pdf_full_list(self):
        test_pdf = "test_full_list.pdf"
        try:
            self.export_service.export_pdf_full_list(test_pdf)
            self.assertTrue(os.path.exists(test_pdf))
            self.assertTrue(os.path.getsize(test_pdf) > 1000)
        finally:
            if os.path.exists(test_pdf):
                os.remove(test_pdf)

    def test_export_individual_reports_pdf(self):
        test_pdf = "test_individual.pdf"
        try:
            self.export_service.export_individual_reports(test_pdf)
            self.assertTrue(os.path.exists(test_pdf))
            self.assertTrue(os.path.getsize(test_pdf) > 1000)
        finally:
            if os.path.exists(test_pdf):
                os.remove(test_pdf)

    def test_export_individual_reports_invalid_extension(self):
        with self.assertRaises(ValueError):
            self.export_service.export_individual_reports("output.txt")


class TestIndividualPdfExporter(unittest.TestCase):
    def setUp(self):
        self.competition = Competition(title="Test Competition")
        self.p1 = Participant(name="John Doe", startnumber=1)
        self.p1.total_points = 100.0
        self.p1.overall_rank = 1
        self.p1.set_result("acc", 15.0)
        self.p1.set_points("acc", 50.0)
        self.p1.set_rank("acc", 1)
        self.competition.add_participant(self.p1)

        class MockDisc:
            def __init__(self, code, label):
                self.code = code
                self.label = label

        disciplines = [MockDisc("acc", "Accuracy")]
        disciplines_dict = {d.code: d for d in disciplines}
        self.exporter = IndividualPdfExporter(self.competition, disciplines_dict)
        self.page = ParticipantReportPage(self.competition, disciplines_dict)

    # --- build_pdf_styles ---

    def test_build_pdf_styles_returns_five_values(self):
        result = self.exporter.build_pdf_styles()
        self.assertEqual(len(result), 5)

    def test_build_pdf_styles_font_names(self):
        _styles, title_style, h2_style, label_style, text_style = (
            self.exporter.build_pdf_styles()
        )
        self.assertEqual(label_style.fontName, "Helvetica-Bold")
        self.assertEqual(label_style.fontSize, 11)
        self.assertEqual(text_style.fontSize, 11)
        self.assertEqual(title_style.alignment, 1)  # CENTER
        self.assertEqual(h2_style.alignment, 1)

    # --- make_logo ---

    def test_make_logo_none_when_no_path(self):
        self.assertIsNone(self.page.make_logo(None))

    def test_make_logo_none_when_invalid_path(self):
        self.assertIsNone(self.page.make_logo("/nonexistent/logo.png"))

    # --- build_participant_info_table ---

    def test_build_participant_info_table_structure(self):
        from reportlab.platypus import Table

        _styles, _title, _h2, label_style, text_style = (
            self.exporter.build_pdf_styles()
        )
        tbl = self.page.build_info_table(self.p1, label_style, text_style)
        self.assertIsInstance(tbl, Table)
        # Three rows: Name, Total Points, Overall Rank
        self.assertEqual(len(tbl._cellvalues), 3)

    def test_build_participant_info_table_values(self):
        _styles, _title, _h2, label_style, text_style = (
            self.exporter.build_pdf_styles()
        )
        tbl = self.page.build_info_table(self.p1, label_style, text_style)
        rows = tbl._cellvalues
        # Each cell is a Paragraph; check the text content
        self.assertIn("John Doe", rows[0][1].text)
        self.assertIn("100", rows[1][1].text)
        self.assertIn("1", rows[2][1].text)

    # --- build_discipline_table ---

    def test_build_discipline_table_structure(self):
        from reportlab.platypus import Table

        self.competition.active_disciplines = {"acc"}
        tbl = self.page.build_discipline_table(self.p1)
        self.assertIsInstance(tbl, Table)
        # Header row + 1 discipline row
        self.assertEqual(len(tbl._cellvalues), 2)

    def test_build_discipline_table_header_row(self):
        self.competition.active_disciplines = {"acc"}
        tbl = self.page.build_discipline_table(self.p1)
        header = tbl._cellvalues[0]
        self.assertEqual(header, ["Discipline", "Result", "Points", "Rank"])

    def test_build_discipline_table_data_row(self):
        self.competition.active_disciplines = {"acc"}
        tbl = self.page.build_discipline_table(self.p1)
        row = tbl._cellvalues[1]
        self.assertEqual(row[0], "Accuracy")
        self.assertEqual(row[1], "15")
        self.assertEqual(row[2], "50")
        self.assertEqual(row[3], "1")

    def test_build_discipline_table_skips_inactive_disciplines(self):
        self.competition.active_disciplines = set()
        tbl = self.page.build_discipline_table(self.p1)
        # Only the header row, no data rows
        self.assertEqual(len(tbl._cellvalues), 1)

    # --- build_participant_page ---

    def test_build_participant_page_element_count(self):
        self.competition.active_disciplines = {"acc"}
        _styles, title_style, h2_style, label_style, text_style = (
            self.exporter.build_pdf_styles()
        )
        elements = self.exporter.build_participant_page(
            self.p1, "Test Competition", None,
            title_style, h2_style, label_style, text_style,
        )
        # Title, Spacer, h2 paragraph, Spacer, Spacer(logo skipped),
        # info table, Spacer, discipline table = 8 elements
        self.assertEqual(len(elements), 8)

    def test_build_participant_page_no_logo_when_path_is_none(self):
        from reportlab.platypus import Image

        self.competition.active_disciplines = {"acc"}
        _styles, title_style, h2_style, label_style, text_style = (
            self.exporter.build_pdf_styles()
        )
        elements = self.exporter.build_participant_page(
            self.p1, "Test Competition", None,
            title_style, h2_style, label_style, text_style,
        )
        self.assertFalse(any(isinstance(e, Image) for e in elements))


class TestParticipantReportPage(unittest.TestCase):
    def setUp(self):
        self.competition = Competition(title="Test Competition")
        self.p1 = Participant(name="John Doe", startnumber=1)
        self.p1.total_points = 100.0
        self.p1.overall_rank = 1
        self.p1.set_result("acc", 15.0)
        self.p1.set_points("acc", 50.0)
        self.p1.set_rank("acc", 1)
        self.competition.add_participant(self.p1)

        class MockDisc:
            def __init__(self, code, label):
                self.code = code
                self.label = label

        disciplines = [MockDisc("acc", "Accuracy")]
        disciplines_dict = {d.code: d for d in disciplines}
        self.page = ParticipantReportPage(self.competition, disciplines_dict)

    def _styles(self):
        from boomerang_score.services.individual_pdf_exporter import IndividualPdfExporter
        exporter = IndividualPdfExporter(self.competition, self.page.disciplines)
        _, title_style, h2_style, label_style, text_style = exporter.build_pdf_styles()
        return title_style, h2_style, label_style, text_style

    # --- make_logo ---

    def test_make_logo_none_when_no_path(self):
        self.assertIsNone(self.page.make_logo(None))

    def test_make_logo_none_when_invalid_path(self):
        self.assertIsNone(self.page.make_logo("/nonexistent/logo.png"))

    # --- build_info_table ---

    def test_build_info_table_structure(self):
        from reportlab.platypus import Table
        _, _, label_style, text_style = self._styles()
        tbl = self.page.build_info_table(self.p1, label_style, text_style)
        self.assertIsInstance(tbl, Table)
        self.assertEqual(len(tbl._cellvalues), 3)

    def test_build_info_table_values(self):
        _, _, label_style, text_style = self._styles()
        tbl = self.page.build_info_table(self.p1, label_style, text_style)
        rows = tbl._cellvalues
        self.assertIn("John Doe", rows[0][1].text)
        self.assertIn("100", rows[1][1].text)
        self.assertIn("1", rows[2][1].text)

    # --- build_discipline_table ---

    def test_build_discipline_table_structure(self):
        from reportlab.platypus import Table
        self.competition.active_disciplines = {"acc"}
        tbl = self.page.build_discipline_table(self.p1)
        self.assertIsInstance(tbl, Table)
        self.assertEqual(len(tbl._cellvalues), 2)

    def test_build_discipline_table_header_row(self):
        self.competition.active_disciplines = {"acc"}
        tbl = self.page.build_discipline_table(self.p1)
        self.assertEqual(tbl._cellvalues[0], ["Discipline", "Result", "Points", "Rank"])

    def test_build_discipline_table_data_row(self):
        self.competition.active_disciplines = {"acc"}
        tbl = self.page.build_discipline_table(self.p1)
        row = tbl._cellvalues[1]
        self.assertEqual(row[0], "Accuracy")
        self.assertEqual(row[1], "15")
        self.assertEqual(row[2], "50")
        self.assertEqual(row[3], "1")

    def test_build_discipline_table_skips_inactive_disciplines(self):
        self.competition.active_disciplines = set()
        tbl = self.page.build_discipline_table(self.p1)
        self.assertEqual(len(tbl._cellvalues), 1)

    # --- build ---

    def test_build_element_count(self):
        self.competition.active_disciplines = {"acc"}
        title_style, h2_style, label_style, text_style = self._styles()
        elements = self.page.build(
            self.p1, "Test Competition", None,
            title_style, h2_style, label_style, text_style,
        )
        self.assertEqual(len(elements), 8)

    def test_build_no_logo_when_path_is_none(self):
        from reportlab.platypus import Image
        self.competition.active_disciplines = {"acc"}
        title_style, h2_style, label_style, text_style = self._styles()
        elements = self.page.build(
            self.p1, "Test Competition", None,
            title_style, h2_style, label_style, text_style,
        )
        self.assertFalse(any(isinstance(e, Image) for e in elements))


if __name__ == "__main__":
    unittest.main()

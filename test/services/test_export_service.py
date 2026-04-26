
import os
import unittest
import csv
from boomerang_score.core.models import Competition, Participant, DisciplineResult
from boomerang_score.services.export_service import ExportService

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
            
        self.assertEqual(len(rows), 3) # Header + 2 participants
        self.assertEqual(rows[0], ["name", "startnumber", "total", "overall_rank"])
        self.assertEqual(rows[1], ["John Doe", "1", "100", "1"])
        self.assertEqual(rows[2], ["Jane Smith", "2", "80", "2"])

    def test_export_csv_with_disciplines(self):
        visible_columns = ["name", "acc_res", "acc_pts", "acc_rank"]
        column_headers = {
            "name": "Name",
            "acc_res": "Acc Result",
            "acc_pts": "Acc Points",
            "acc_rank": "Acc Rank"
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

if __name__ == "__main__":
    unittest.main()

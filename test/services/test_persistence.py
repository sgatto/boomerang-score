import io
import os
import tempfile
import unittest

from boomerang_score.core.models import Competition, Participant
from boomerang_score.services.export_service import ExportService


class MockDisc:
    def __init__(self, code, label):
        self.code = code
        self.label = label


DISCIPLINES = [MockDisc("acc", "ACC"), MockDisc("aus", "AUS")]

# Column headers as the table view produces them
TABLE_COLUMN_HEADERS = {
    "name": "Name",
    "startnumber": "Start No.",
    "total": "Total Points",
    "overall_rank": "Overall Rank",
    "acc_res": "ACC Res",
    "acc_pts": "ACC Pts",
    "acc_rank": "ACC Rank",
    "aus_res": "AUS Res",
    "aus_pts": "AUS Pts",
    "aus_rank": "AUS Rank",
}
ALL_COLUMNS = list(TABLE_COLUMN_HEADERS.keys())


def _make_competition():
    comp = Competition(title="Spring Open 2025")
    p1 = Participant(name="Alice", startnumber=3)
    p1.set_result("acc", 25.0)
    p1.set_result("aus", 90.0)
    p1.total_points = 500.0
    p1.overall_rank = 1
    comp.add_participant(p1)

    p2 = Participant(name="Bob", startnumber=7)
    p2.set_result("acc", 18.0)
    # Bob has no AUS result
    p2.total_points = 300.0
    p2.overall_rank = 2
    comp.add_participant(p2)

    return comp


class TestLoadCsvFormatDetection(unittest.TestCase):
    """load_csv() must handle both the auto-save format (with title block) and the plain export format."""

    def setUp(self):
        self.comp = _make_competition()
        self.svc = ExportService(self.comp, DISCIPLINES)
        self.tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        self.tmp.close()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_load_with_header_block(self):
        self.svc.export_csv(self.tmp.name, ALL_COLUMNS, TABLE_COLUMN_HEADERS,
                            list(self.comp.participants), include_header=True)
        data = self.svc.load_csv(self.tmp.name)
        self.assertEqual(data["title"], "Spring Open 2025")
        self.assertEqual(len(data["participants"]), 2)

    def test_load_without_header_block(self):
        self.svc.export_csv(self.tmp.name, ALL_COLUMNS, TABLE_COLUMN_HEADERS,
                            list(self.comp.participants), include_header=False)
        data = self.svc.load_csv(self.tmp.name)
        # No title row present → falls back to default
        self.assertEqual(data["title"], "My Competition")
        self.assertEqual(len(data["participants"]), 2)

    def test_empty_file_raises(self):
        open(self.tmp.name, "w").close()
        with self.assertRaises(ValueError):
            self.svc.load_csv(self.tmp.name)

    def test_truncated_header_block_raises(self):
        with open(self.tmp.name, "w", encoding="utf-8") as f:
            f.write("Titel;My Comp\n")  # Only 1 row, not the expected 4+
        with self.assertRaises(ValueError):
            self.svc.load_csv(self.tmp.name)


class TestStartnumberRoundtrip(unittest.TestCase):
    """Startnumbers must survive a save/load cycle when the CSV uses 'Start No.' as the column header."""

    def setUp(self):
        self.comp = _make_competition()
        self.svc = ExportService(self.comp, DISCIPLINES)
        self.tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        self.tmp.close()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def _load_participants(self, include_header):
        self.svc.export_csv(self.tmp.name, ALL_COLUMNS, TABLE_COLUMN_HEADERS,
                            list(self.comp.participants), include_header=include_header)
        data = self.svc.load_csv(self.tmp.name)

        # Simulate the key-normalisation the GUI does
        def _normalize(k):
            return k.strip().lower()

        results = {}
        for row in data["participants"]:
            norm = {_normalize(k): v for k, v in row.items()}
            startnr = None
            for k in ["startnummer", "startnr", "start no.", "start no", "start", "startnr.", "startnumber"]:
                if k in norm and norm[k].strip():
                    try:
                        startnr = int(float(norm[k]))
                        break
                    except ValueError:
                        continue
            name = norm.get("name", "")
            results[name] = startnr
        return results

    def test_startnumbers_preserved_with_header_block(self):
        result = self._load_participants(include_header=True)
        self.assertEqual(result["Alice"], 3)
        self.assertEqual(result["Bob"], 7)

    def test_startnumbers_preserved_without_header_block(self):
        result = self._load_participants(include_header=False)
        self.assertEqual(result["Alice"], 3)
        self.assertEqual(result["Bob"], 7)


class TestMissingDisciplineResults(unittest.TestCase):
    """Participants without a result for a discipline must not have 0.0 injected."""

    def setUp(self):
        self.comp = _make_competition()
        self.svc = ExportService(self.comp, DISCIPLINES)
        self.tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        self.tmp.close()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_missing_result_column_not_zero(self):
        self.svc.export_csv(self.tmp.name, ALL_COLUMNS, TABLE_COLUMN_HEADERS,
                            list(self.comp.participants), include_header=True)
        data = self.svc.load_csv(self.tmp.name)

        def _normalize(k):
            return k.strip().lower()

        bob_row = next(
            {_normalize(k): v for k, v in row.items()}
            for row in data["participants"]
            if row.get("Name", "").strip() == "Bob"
        )

        # Bob has no AUS result — the cell should be empty in the CSV
        aus_res_value = bob_row.get("aus res", "").strip()
        self.assertEqual(aus_res_value, "",
                         "Missing AUS result should be empty string, not '0'")

    def test_present_result_preserved(self):
        self.svc.export_csv(self.tmp.name, ALL_COLUMNS, TABLE_COLUMN_HEADERS,
                            list(self.comp.participants), include_header=True)
        data = self.svc.load_csv(self.tmp.name)

        def _normalize(k):
            return k.strip().lower()

        alice_row = next(
            {_normalize(k): v for k, v in row.items()}
            for row in data["participants"]
            if row.get("Name", "").strip() == "Alice"
        )
        self.assertEqual(alice_row.get("acc res", "").strip(), "25")
        self.assertEqual(alice_row.get("aus res", "").strip(), "90")


if __name__ == "__main__":
    unittest.main()

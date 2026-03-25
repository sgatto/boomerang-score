"""Unit tests for CompetitionService."""

import pytest
from boomerang_score.core import Competition, ACC, AUS, MTA
from boomerang_score.services import CompetitionService


@pytest.fixture
def competition():
    """Create a fresh competition for each test."""
    return Competition()


@pytest.fixture
def service(competition):
    """Create a competition service with ACC, AUS, MTA disciplines."""
    comp = competition
    comp.set_active_disciplines({"acc", "aus", "mta"})
    return CompetitionService(comp, [ACC, AUS, MTA])


class TestAddParticipant:
    """Tests for adding participants."""

    def test_add_participant(self, service, competition):
        service.add_participant("p1", "John Doe", 1, {"acc": 50.0, "aus": 90.0, "mta": 30.0})

        assert len(competition.participants) == 1
        p = competition.get_participant("p1")
        assert p.name == "John Doe"
        assert p.startnumber == 1
        assert p.get_result("acc") == 50.0

    def test_add_participant_calculates_points(self, service, competition):
        service.add_participant("p1", "John", 1, {"acc": 50.0})

        p = competition.get_participant("p1")
        # ACC: 50 seconds should give points (check scorer.py for formula)
        assert p.get_points("acc") is not None
        assert p.get_points("acc") > 0

    def test_add_participant_calculates_total(self, service, competition):
        service.add_participant("p1", "John", 1, {"acc": 50.0, "aus": 90.0})

        p = competition.get_participant("p1")
        assert p.total_points is not None
        assert p.total_points > 0

    def test_add_participant_with_duplicate_startnumber_auto_assigns(self, service, competition):
        service.add_participant("p1", "John", 1, {})
        service.add_participant("p2", "Jane", 1, {})  # Same startnumber

        p1 = competition.get_participant("p1")
        p2 = competition.get_participant("p2")
        assert p1.startnumber == 1
        assert p2.startnumber == 2  # Auto-assigned

    def test_add_multiple_participants_calculates_ranks(self, service, competition):
        service.add_participant("p1", "John", 1, {"acc": 50.0})
        service.add_participant("p2", "Jane", 2, {"acc": 75.0})  # Better score (higher)
        service.add_participant("p3", "Bob", 3, {"acc": 40.0})   # Worse score (lower)

        p1 = competition.get_participant("p1")
        p2 = competition.get_participant("p2")
        p3 = competition.get_participant("p3")

        # In ACC (Accuracy), higher score = better rank (lower number)
        # 75 > 50 > 40, so Jane should have best rank
        assert p2.get_rank("acc") < p1.get_rank("acc")
        assert p1.get_rank("acc") < p3.get_rank("acc")


class TestUpdateParticipant:
    """Tests for updating participants."""

    def test_update_participant_name(self, service, competition):
        service.add_participant("p1", "John Doe", 1, {})
        service.update_participant_name("p1", "Jane Smith")

        p = competition.get_participant("p1")
        assert p.name == "Jane Smith"

    def test_update_name_empty_raises_error(self, service, competition):
        service.add_participant("p1", "John", 1, {})

        with pytest.raises(ValueError, match="cannot be empty"):
            service.update_participant_name("p1", "")

    def test_update_nonexistent_participant_raises_error(self, service, competition):
        with pytest.raises(ValueError, match="not found"):
            service.update_participant_name("p999", "Test")

    def test_update_startnumber(self, service, competition):
        service.add_participant("p1", "John", 1, {})
        service.update_participant_startnumber("p1", 42)

        p = competition.get_participant("p1")
        assert p.startnumber == 42

    def test_update_startnumber_duplicate_raises_error(self, service, competition):
        service.add_participant("p1", "John", 1, {})
        service.add_participant("p2", "Jane", 2, {})

        with pytest.raises(ValueError, match="already assigned"):
            service.update_participant_startnumber("p2", 1)

    def test_update_result(self, service, competition):
        service.add_participant("p1", "John", 1, {"acc": 50.0})
        service.update_participant_result("p1", "acc", 45.0)

        p = competition.get_participant("p1")
        assert p.get_result("acc") == 45.0

    def test_update_result_recalculates_points(self, service, competition):
        service.add_participant("p1", "John", 1, {"acc": 50.0})
        old_points = competition.get_participant("p1").get_points("acc")

        service.update_participant_result("p1", "acc", 45.0)
        new_points = competition.get_participant("p1").get_points("acc")

        assert new_points != old_points

    def test_update_result_recalculates_ranks(self, service, competition):
        service.add_participant("p1", "John", 1, {"acc": 50.0})
        service.add_participant("p2", "Jane", 2, {"acc": 45.0})

        p1 = competition.get_participant("p1")
        p2 = competition.get_participant("p2")

        # Initially p1 is better (50 > 45)
        assert p1.get_rank("acc") < p2.get_rank("acc")

        # Update p1 to have better score
        service.update_participant_result("p1", "acc", 80.0)

        # Now p1 should be even better
        assert p1.get_rank("acc") == 1

    def test_update_unknown_discipline_raises_error(self, service, competition):
        service.add_participant("p1", "John", 1, {})

        with pytest.raises(ValueError, match="Unknown discipline"):
            service.update_participant_result("p1", "unknown", 50.0)


class TestActiveDisciplines:
    """Tests for managing active disciplines."""

    def test_set_active_disciplines(self, service, competition):
        service.set_active_disciplines({"acc", "aus"})
        assert competition.active_disciplines == {"acc", "aus"}

    def test_changing_active_disciplines_recalculates_totals(self, service, competition):
        # Add participant with results in all disciplines
        service.add_participant("p1", "John", 1, {"acc": 50.0, "aus": 90.0, "mta": 30.0})

        p = competition.get_participant("p1")
        total_with_all = p.total_points

        # Deactivate one discipline
        service.set_active_disciplines({"acc", "aus"})  # Remove mta

        total_without_mta = p.total_points
        assert total_without_mta < total_with_all

    def test_inactive_disciplines_have_no_rank(self, service, competition):
        service.add_participant("p1", "John", 1, {"acc": 50.0, "aus": 90.0, "mta": 30.0})

        # Deactivate aus
        service.set_active_disciplines({"acc", "mta"})

        p = competition.get_participant("p1")
        assert p.get_rank("acc") is not None
        assert p.get_rank("aus") is None  # Inactive
        assert p.get_rank("mta") is not None


class TestRecalculation:
    """Tests for recalculation methods."""

    def test_recalculate_participant(self, service, competition):
        service.add_participant("p1", "John", 1, {"acc": 50.0})

        # Manually change result (bypassing service)
        p = competition.get_participant("p1")
        p.set_result("acc", 45.0)

        # Recalculate
        service.recalculate_participant("p1")

        # Points should be updated
        assert p.get_points("acc") is not None

    def test_recalculate_all_ranks(self, service, competition):
        service.add_participant("p1", "John", 1, {"acc": 50.0})
        service.add_participant("p2", "Jane", 2, {"acc": 45.0})

        # Manually change result
        p1 = competition.get_participant("p1")
        p1.set_result("acc", 40.0)

        # Recalculate points and ranks
        service.recalculate_participant("p1")
        service.recalculate_all_ranks()

        # P1 now has worse score (40 < 45), so p2 should have better rank
        p2 = competition.get_participant("p2")
        assert p2.get_rank("acc") < p1.get_rank("acc")

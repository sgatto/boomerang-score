"""Unit tests for CompetitionService."""

import pytest
from boomerang_score.core import Competition, ACC, AUS, MTA
from boomerang_score.core.constants import DISC_CODE_ACC, DISC_CODE_AUS, DISC_CODE_MTA
from boomerang_score.services import CompetitionService


@pytest.fixture
def competition():
    """Create a fresh competition for each test."""
    return Competition()


@pytest.fixture
def service(competition):
    """Create a competition service with ACC, AUS, MTA disciplines."""
    comp = competition
    comp.set_active_disciplines({DISC_CODE_ACC, DISC_CODE_AUS, DISC_CODE_MTA})
    return CompetitionService(comp, [ACC, AUS, MTA])


class TestAddParticipant:
    """Tests for adding participants."""

    def test_add_participant(self, service, competition):
        participant = service.add_participant("John Doe", 1, {DISC_CODE_ACC: 50.0, DISC_CODE_AUS: 90.0, DISC_CODE_MTA: 30.0})

        assert len(competition.participants) == 1
        p = competition.get_participant(1)
        assert p.name == "John Doe"
        assert p.startnumber == 1
        assert p.get_result(DISC_CODE_ACC) == 50.0

    def test_add_participant_calculates_points(self, service, competition):
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0})

        p = competition.get_participant(1)
        # ACC: 50 seconds should give points (check scorer.py for formula)
        assert p.get_points(DISC_CODE_ACC) is not None
        assert p.get_points(DISC_CODE_ACC) > 0

    def test_add_participant_calculates_total(self, service, competition):
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0, DISC_CODE_AUS: 90.0})

        p = competition.get_participant(1)
        assert p.total_points is not None
        assert p.total_points > 0

    def test_add_participant_with_duplicate_startnumber_raises_error(self, service, competition):
        service.add_participant("John", 1, {})

        with pytest.raises(ValueError, match="already assigned"):
            service.add_participant("Jane", 1, {})  # Same startnumber should raise

    def test_add_multiple_participants_calculates_ranks(self, service, competition):
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0})
        service.add_participant("Jane", 2, {DISC_CODE_ACC: 75.0})  # Better score (higher)
        service.add_participant("Bob", 3, {DISC_CODE_ACC: 40.0})   # Worse score (lower)

        p1 = competition.get_participant(1)
        p2 = competition.get_participant(2)
        p3 = competition.get_participant(3)

        # In ACC (Accuracy), higher score = better rank (lower number)
        # 75 > 50 > 40, so Jane should have best rank
        assert p2.get_rank(DISC_CODE_ACC) < p1.get_rank(DISC_CODE_ACC)
        assert p1.get_rank(DISC_CODE_ACC) < p3.get_rank(DISC_CODE_ACC)


class TestUpdateParticipant:
    """Tests for updating participants."""

    def test_update_participant_name(self, service, competition):
        service.add_participant("John Doe", 1, {})
        service.update_participant_name(1, "Jane Smith")

        p = competition.get_participant(1)
        assert p.name == "Jane Smith"

    def test_update_name_empty_raises_error(self, service, competition):
        service.add_participant("John", 1, {})

        with pytest.raises(ValueError, match="cannot be empty"):
            service.update_participant_name(1, "")

    def test_update_nonexistent_participant_raises_error(self, service, competition):
        with pytest.raises(ValueError, match="not found"):
            service.update_participant_name(999, "Test")

    def test_change_startnumber(self, service, competition):
        service.add_participant("John Doe", 1, {DISC_CODE_ACC: 50.0})
        service.add_participant("Jane Doe", 2, {DISC_CODE_ACC: 60.0})

        # Change John's startnumber from 1 to 3
        service.change_startnumber(1, 3)

        assert competition.get_participant(1) is None
        p = competition.get_participant(3)
        assert p is not None
        assert p.name == "John Doe"
        assert p.startnumber == 3
        assert p.get_result(DISC_CODE_ACC) == 50.0

        # Ranks should be preserved/recalculated correctly
        assert p.get_rank(DISC_CODE_ACC) == 2  # 50 < 60
        assert competition.get_participant(2).get_rank(DISC_CODE_ACC) == 1

    def test_change_startnumber_to_existing_raises_error(self, service, competition):
        service.add_participant("John", 1, {})
        service.add_participant("Jane", 2, {})

        with pytest.raises(ValueError, match="already assigned"):
            service.change_startnumber(1, 2)

    def test_change_startnumber_nonexistent_raises_error(self, service):
        with pytest.raises(ValueError, match="not found"):
            service.change_startnumber(999, 10)

    def test_change_startnumber_to_same_does_nothing(self, service, competition):
        service.add_participant("John", 1, {})
        service.change_startnumber(1, 1)
        assert competition.get_participant(1) is not None

    def test_update_result(self, service, competition):
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0})
        service.update_participant_result(1, DISC_CODE_ACC, 45.0)

        p = competition.get_participant(1)
        assert p.get_result(DISC_CODE_ACC) == 45.0

    def test_update_result_recalculates_points(self, service, competition):
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0})
        old_points = competition.get_participant(1).get_points(DISC_CODE_ACC)

        service.update_participant_result(1, DISC_CODE_ACC, 45.0)
        new_points = competition.get_participant(1).get_points(DISC_CODE_ACC)

        assert new_points != old_points

    def test_update_result_recalculates_ranks(self, service, competition):
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0})
        service.add_participant("Jane", 2, {DISC_CODE_ACC: 45.0})

        p1 = competition.get_participant(1)
        p2 = competition.get_participant(2)

        # Initially p1 is better (50 > 45)
        assert p1.get_rank(DISC_CODE_ACC) < p2.get_rank(DISC_CODE_ACC)

        # Update p1 to have better score
        service.update_participant_result(1, DISC_CODE_ACC, 80.0)

        # Now p1 should be even better
        assert p1.get_rank(DISC_CODE_ACC) == 1

    def test_update_unknown_discipline_raises_error(self, service, competition):
        service.add_participant("John", 1, {})

        with pytest.raises(ValueError, match="Unknown discipline"):
            service.update_participant_result(1, "unknown", 50.0)


class TestActiveDisciplines:
    """Tests for managing active disciplines."""

    def test_set_active_disciplines(self, service, competition):
        service.set_active_disciplines({DISC_CODE_ACC, DISC_CODE_AUS})
        assert competition.active_disciplines == {DISC_CODE_ACC, DISC_CODE_AUS}

    def test_changing_active_disciplines_recalculates_totals(self, service, competition):
        # Add participant with results in all disciplines
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0, DISC_CODE_AUS: 90.0, DISC_CODE_MTA: 30.0})

        p = competition.get_participant(1)
        total_with_all = p.total_points

        # Deactivate one discipline
        service.set_active_disciplines({DISC_CODE_ACC, DISC_CODE_AUS})  # Remove mta

        total_without_mta = p.total_points
        assert total_without_mta < total_with_all

    def test_inactive_disciplines_have_no_rank(self, service, competition):
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0, DISC_CODE_AUS: 90.0, DISC_CODE_MTA: 30.0})

        # Deactivate aus
        service.set_active_disciplines({DISC_CODE_ACC, DISC_CODE_MTA})

        p = competition.get_participant(1)
        assert p.get_rank(DISC_CODE_ACC) is not None
        assert p.get_rank(DISC_CODE_AUS) is None  # Inactive
        assert p.get_rank(DISC_CODE_MTA) is not None


class TestRecalculation:
    """Tests for recalculation methods."""

    def test_recalculate_participant(self, service, competition):
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0})

        # Manually change result (bypassing service)
        p = competition.get_participant(1)
        p.set_result(DISC_CODE_ACC, 45.0)

        # Recalculate
        service.recalculate_participant(1)

        # Points should be updated
        assert p.get_points(DISC_CODE_ACC) is not None

    def test_recalculate_all_ranks(self, service, competition):
        service.add_participant("John", 1, {DISC_CODE_ACC: 50.0})
        service.add_participant("Jane", 2, {DISC_CODE_ACC: 45.0})

        # Manually change result
        p1 = competition.get_participant(1)
        p1.set_result(DISC_CODE_ACC, 40.0)

        # Recalculate points and ranks
        service.recalculate_participant(1)
        service.recalculate_all_ranks()

        # P1 now has worse score (40 < 45), so p2 should have better rank
        p2 = competition.get_participant(2)
        assert p2.get_rank(DISC_CODE_ACC) < p1.get_rank(DISC_CODE_ACC)


class TestDeleteParticipant:
    """Tests for deleting participants."""

    def test_delete_participant(self, service, competition):
        service.add_participant("John Doe", 1, {})
        assert len(competition.participants) == 1

        service.delete_participant(1)
        assert len(competition.participants) == 0

    def test_delete_participant_recalculates_ranks(self, service, competition):
        service.add_participant("First", 1, {DISC_CODE_ACC: 100.0})
        service.add_participant("Second", 2, {DISC_CODE_ACC: 50.0})
        service.add_participant("Third", 3, {DISC_CODE_ACC: 25.0})

        p2 = competition.get_participant(2)
        p3 = competition.get_participant(3)

        assert p2.get_rank(DISC_CODE_ACC) == 2
        assert p3.get_rank(DISC_CODE_ACC) == 3

        # Delete the first one
        service.delete_participant(1)

        # Now "Second" should be 1st, "Third" should be 2nd
        assert p2.get_rank(DISC_CODE_ACC) == 1
        assert p3.get_rank(DISC_CODE_ACC) == 2

    def test_delete_nonexistent_participant_raises_error(self, service):
        with pytest.raises(ValueError, match="not found"):
            service.delete_participant(999)


class TestClearData:
    """Tests for clearing competition data."""

    def test_clear_all_data(self, service, competition):
        competition.title = "Special Competition"
        competition.logo_path = "/path/to/logo.png"
        service.add_participant("Test", 1, {"acc": 10.0})

        assert len(competition.participants) == 1
        assert competition.title == "Special Competition"
        assert competition.logo_path == "/path/to/logo.png"

        service.clear_all_data()

        assert len(competition.participants) == 0
        assert competition.title == "My Competition"
        assert competition.logo_path is None

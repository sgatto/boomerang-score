"""Unit tests for domain models."""

import pytest
from boomerang_score.core.models import Participant, Competition, DisciplineResult


class TestDisciplineResult:
    """Tests for DisciplineResult dataclass."""

    def test_create_with_all_values(self):
        result = DisciplineResult(result=45.5, points=88.2, rank=3)
        assert result.result == 45.5
        assert result.points == 88.2
        assert result.rank == 3

    def test_create_with_none_values(self):
        result = DisciplineResult()
        assert result.result is None
        assert result.points is None
        assert result.rank is None

    def test_converts_to_float(self):
        result = DisciplineResult(result="45.5", points="88")
        assert result.result == 45.5
        assert result.points == 88.0

    def test_converts_rank_to_int(self):
        result = DisciplineResult(rank="3")
        assert result.rank == 3
        assert isinstance(result.rank, int)


class TestParticipant:
    """Tests for Participant dataclass."""

    def test_create_participant(self):
        p = Participant(name="John Doe", startnumber=42)
        assert p.name == "John Doe"
        assert p.startnumber == 42
        assert p.disciplines == {}
        assert p.total_points is None
        assert p.overall_rank is None

    def test_name_is_trimmed(self):
        p = Participant(name="  John Doe  ", startnumber=1)
        assert p.name == "John Doe"

    def test_empty_name_raises_error(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Participant(name="", startnumber=1)

    def test_whitespace_name_raises_error(self):
        with pytest.raises(ValueError, match="name cannot be empty"):
            Participant(name="   ", startnumber=1)

    def test_startnumber_converts_to_int(self):
        p = Participant(name="Test", startnumber="42")
        assert p.startnumber == 42
        assert isinstance(p.startnumber, int)

    def test_set_and_get_result(self):
        p = Participant(name="Test", startnumber=1)
        p.set_result("acc", 45.5)
        assert p.get_result("acc") == 45.5

    def test_get_result_nonexistent_returns_none(self):
        p = Participant(name="Test", startnumber=1)
        assert p.get_result("acc") is None

    def test_set_and_get_points(self):
        p = Participant(name="Test", startnumber=1)
        p.set_points("acc", 88.5)
        assert p.get_points("acc") == 88.5

    def test_set_and_get_rank(self):
        p = Participant(name="Test", startnumber=1)
        p.set_rank("acc", 3)
        assert p.get_rank("acc") == 3

    def test_set_result_creates_discipline_entry(self):
        p = Participant(name="Test", startnumber=1)
        p.set_result("acc", 45.5)
        assert "acc" in p.disciplines
        assert p.disciplines["acc"].result == 45.5

    def test_set_none_result(self):
        p = Participant(name="Test", startnumber=1)
        p.set_result("acc", None)
        assert p.get_result("acc") is None


class TestCompetition:
    """Tests for Competition dataclass."""

    def test_create_empty_competition(self):
        comp = Competition()
        assert comp.title == "My Competition"
        assert comp.logo_path is None
        assert comp.participants == {}
        assert comp.active_disciplines == set()

    def test_create_with_title(self):
        comp = Competition(title="Test Tournament")
        assert comp.title == "Test Tournament"

    def test_add_participant(self):
        comp = Competition()
        p = Participant(name="John", startnumber=1)
        comp.add_participant(p)
        assert 1 in comp.participants
        assert comp.participants[1] == p

    def test_add_duplicate_participant_raises_error(self):
        comp = Competition()
        p1 = Participant(name="John", startnumber=1)
        p2 = Participant(name="Jane", startnumber=1)  # Same startnumber
        comp.add_participant(p1)

        with pytest.raises(ValueError, match="already exists"):
            comp.add_participant(p2)

    def test_remove_participant(self):
        comp = Competition()
        p = Participant(name="John", startnumber=1)
        comp.add_participant(p)
        comp.remove_participant(1)
        assert 1 not in comp.participants

    def test_remove_nonexistent_participant_raises_error(self):
        comp = Competition()
        with pytest.raises(ValueError, match="not found"):
            comp.remove_participant(1)

    def test_get_participant(self):
        comp = Competition()
        p = Participant(name="John", startnumber=1)
        comp.add_participant(p)
        result = comp.get_participant(1)
        assert result == p

    def test_get_nonexistent_participant_returns_none(self):
        comp = Competition()
        assert comp.get_participant(1) is None

    def test_set_active_disciplines(self):
        comp = Competition()
        comp.set_active_disciplines({"acc", "aus", "mta"})
        assert comp.active_disciplines == {"acc", "aus", "mta"}

    def test_is_discipline_active(self):
        comp = Competition()
        comp.set_active_disciplines({"acc", "aus"})
        assert comp.is_discipline_active("acc") is True
        assert comp.is_discipline_active("mta") is False

    def test_get_all_participants(self):
        comp = Competition()
        p1 = Participant(name="John", startnumber=1)
        p2 = Participant(name="Jane", startnumber=2)
        comp.add_participant(p1)
        comp.add_participant(p2)

        all_p = comp.get_all_participants()
        assert len(all_p) == 2
        assert p1 in all_p
        assert p2 in all_p

    def test_startnumber_exists(self):
        comp = Competition()
        p1 = Participant(name="John", startnumber=1)
        comp.add_participant(p1)

        assert comp.startnumber_exists(1) is True
        assert comp.startnumber_exists(2) is False

    def test_next_free_startnumber(self):
        comp = Competition()
        assert comp.next_free_startnumber() == 1

        p1 = Participant(name="John", startnumber=1)
        comp.add_participant(p1)
        assert comp.next_free_startnumber() == 2

        p2 = Participant(name="Jane", startnumber=2)
        comp.add_participant(p2)
        assert comp.next_free_startnumber() == 3

    def test_next_free_startnumber_with_gaps(self):
        comp = Competition()
        p1 = Participant(name="John", startnumber=1)
        p3 = Participant(name="Jane", startnumber=3)
        comp.add_participant(p1)
        comp.add_participant(p3)

        # Should return 2 (the gap)
        assert comp.next_free_startnumber() == 2

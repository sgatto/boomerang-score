"""Domain models for boomerang scoring."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DisciplineResult:
    """Result for a single discipline."""
    result: Optional[float] = None  # Raw result (e.g., time, distance)
    points: Optional[float] = None  # Calculated points
    rank: Optional[int] = None      # Rank in this discipline

    def __post_init__(self):
        """Ensure numeric types."""
        if self.result is not None:
            self.result = float(self.result)
        if self.points is not None:
            self.points = float(self.points)
        if self.rank is not None:
            self.rank = int(self.rank)


@dataclass
class Participant:
    """A participant in the competition."""
    name: str
    startnumber: int
    disciplines: dict[str, DisciplineResult] = field(default_factory=dict)
    total_points: Optional[float] = None
    overall_rank: Optional[int] = None

    def __post_init__(self):
        """Validate and normalize data."""
        if not self.name or not self.name.strip():
            raise ValueError("Participant name cannot be empty")
        self.name = self.name.strip()
        self.startnumber = int(self.startnumber)

    def get_result(self, discipline_code: str) -> Optional[float]:
        """Get raw result for a discipline."""
        if discipline_code not in self.disciplines:
            return None
        return self.disciplines[discipline_code].result

    def set_result(self, discipline_code: str, result: Optional[float]):
        """Set raw result for a discipline."""
        if discipline_code not in self.disciplines:
            self.disciplines[discipline_code] = DisciplineResult()
        self.disciplines[discipline_code].result = float(result) if result is not None else None

    def get_points(self, discipline_code: str) -> Optional[float]:
        """Get calculated points for a discipline."""
        if discipline_code not in self.disciplines:
            return None
        return self.disciplines[discipline_code].points

    def set_points(self, discipline_code: str, points: Optional[float]):
        """Set calculated points for a discipline."""
        if discipline_code not in self.disciplines:
            self.disciplines[discipline_code] = DisciplineResult()
        self.disciplines[discipline_code].points = float(points) if points is not None else None

    def get_rank(self, discipline_code: str) -> Optional[int]:
        """Get rank for a discipline."""
        if discipline_code not in self.disciplines:
            return None
        return self.disciplines[discipline_code].rank

    def set_rank(self, discipline_code: str, rank: Optional[int]):
        """Set rank for a discipline."""
        if discipline_code not in self.disciplines:
            self.disciplines[discipline_code] = DisciplineResult()
        self.disciplines[discipline_code].rank = int(rank) if rank is not None else None


@dataclass
class Competition:
    """A competition with participants and active disciplines."""
    title: str = "My Competition"
    logo_path: Optional[str] = None
    participants: dict[str, Participant] = field(default_factory=dict)
    active_disciplines: set[str] = field(default_factory=set)

    def add_participant(self, participant_id: str, participant: Participant):
        """Add a participant to the competition."""
        if participant_id in self.participants:
            raise ValueError(f"Participant with ID {participant_id} already exists")
        self.participants[participant_id] = participant

    def remove_participant(self, participant_id: str):
        """Remove a participant from the competition."""
        if participant_id not in self.participants:
            raise ValueError(f"Participant with ID {participant_id} not found")
        del self.participants[participant_id]

    def get_participant(self, participant_id: str) -> Optional[Participant]:
        """Get a participant by ID."""
        return self.participants.get(participant_id)

    def set_active_disciplines(self, discipline_codes: set[str]):
        """Set which disciplines are active."""
        self.active_disciplines = set(discipline_codes)

    def is_discipline_active(self, discipline_code: str) -> bool:
        """Check if a discipline is active."""
        return discipline_code in self.active_disciplines

    def get_all_participants(self) -> list[Participant]:
        """Get all participants as a list."""
        return list(self.participants.values())

    def startnumber_exists(self, startnumber: int, exclude_id: Optional[str] = None) -> bool:
        """Check if a startnumber is already used."""
        for pid, p in self.participants.items():
            if pid != exclude_id and p.startnumber == startnumber:
                return True
        return False

    def next_free_startnumber(self) -> int:
        """Get the next available startnumber."""
        used = {p.startnumber for p in self.participants.values()}
        n = 1
        while n in used:
            n += 1
        return n

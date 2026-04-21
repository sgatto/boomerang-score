"""Business logic for managing competitions."""

from boomerang_score.core.models import Competition, Participant
from boomerang_score.core.scorer import compute_competition_ranks


class CompetitionService:
    """Service for managing competition business logic."""

    def __init__(self, competition: Competition, disciplines):
        """
        Initialize the service.

        Args:
            competition: The Competition instance to manage
            disciplines: List of discipline definitions (from scorer.py)
        """
        self.competition = competition
        self.disciplines = {d.code: d for d in disciplines}

    def add_participant(self, name: str, startnumber: int,
                       discipline_results: dict[str, float]) -> Participant:
        """
        Add a new participant to the competition.

        Args:
            name: Participant name
            startnumber: Start number (immutable, acts as participant ID)
            discipline_results: Dict of {discipline_code: result_value}

        Returns:
            The created Participant

        Raises:
            ValueError: If validation fails or startnumber already exists
        """
        # Validate startnumber is unique
        if self.competition.startnumber_exists(startnumber):
            raise ValueError(f"Startnumber {startnumber} is already assigned")

        # Create participant
        participant = Participant(name=name, startnumber=startnumber)

        # Set results for all disciplines
        for disc_code, result in discipline_results.items():
            if disc_code in self.disciplines:
                participant.set_result(disc_code, result)

        # Add to competition
        self.competition.add_participant(participant)

        # Calculate points and ranks
        self.recalculate_participant(startnumber)
        self.recalculate_all_ranks()

        return participant

    def delete_participant(self, startnumber: int):
        """
        Delete a participant from the competition.

        Args:
            startnumber: Participant startnumber (ID)
        """
        if not self.competition.startnumber_exists(startnumber):
            raise ValueError(f"Participant with startnumber {startnumber} not found")

        # Remove from competition
        self.competition.remove_participant(startnumber)

        # Recalculate all ranks (ranks change when a participant is removed)
        self.recalculate_all_ranks()

    def update_participant_name(self, startnumber: int, name: str):
        """Update participant name."""
        participant = self.competition.get_participant(startnumber)
        if not participant:
            raise ValueError(f"Participant with startnumber {startnumber} not found")

        if not name or not name.strip():
            raise ValueError("Name cannot be empty")

        participant.name = name.strip()

    def update_participant_result(self, startnumber: int, discipline_code: str, result: float):
        """
        Update a participant's result for a discipline.

        Args:
            startnumber: Participant startnumber (ID)
            discipline_code: Discipline code (e.g., 'acc', 'aus')
            result: New result value
        """
        participant = self.competition.get_participant(startnumber)
        if not participant:
            raise ValueError(f"Participant with startnumber {startnumber} not found")

        if discipline_code not in self.disciplines:
            raise ValueError(f"Unknown discipline: {discipline_code}")

        # Update result
        participant.set_result(discipline_code, result)

        # Recalculate points and ranks
        self.recalculate_participant(startnumber)
        self.recalculate_all_ranks()

    def recalculate_participant(self, startnumber: int):
        """Recalculate points and total for a single participant."""
        participant = self.competition.get_participant(startnumber)
        if not participant:
            return

        total = 0.0

        # Calculate points for each discipline
        for disc_code, discipline in self.disciplines.items():
            result = participant.get_result(disc_code)
            if result is not None:
                points = discipline.points_func(result)
                participant.set_points(disc_code, points)

                # Add to total only if discipline is active
                if self.competition.is_discipline_active(disc_code):
                    total += points
            else:
                participant.set_points(disc_code, 0.0)

        participant.total_points = total

    def recalculate_all_ranks(self):
        """Recalculate ranks for all disciplines and overall."""
        # Recalculate discipline ranks (only for active disciplines)
        for disc_code, discipline in self.disciplines.items():
            if not self.competition.is_discipline_active(disc_code):
                # Clear ranks for inactive disciplines
                for participant in self.competition.get_all_participants():
                    participant.set_rank(disc_code, None)
                continue

            # Prepare items for ranking
            if disc_code == "fc":
                # Fastcatch uses points for ranking
                items = [
                    (startnr, p.get_points(disc_code))
                    for startnr, p in self.competition.participants.items()
                ]
            else:
                # Other disciplines use results
                items = [
                    (startnr, p.get_result(disc_code))
                    for startnr, p in self.competition.participants.items()
                ]

            # Compute ranks
            ranks = compute_competition_ranks(items)

            # Apply ranks
            for startnr, rank in ranks.items():
                participant = self.competition.get_participant(startnr)
                if participant:
                    participant.set_rank(disc_code, rank)

        # Recalculate overall ranks based on total points
        items_total = [
            (startnr, p.total_points)
            for startnr, p in self.competition.participants.items()
        ]
        ranks_total = compute_competition_ranks(items_total)

        for startnr, rank in ranks_total.items():
            participant = self.competition.get_participant(startnr)
            if participant:
                participant.overall_rank = rank

    def set_active_disciplines(self, discipline_codes: set[str]):
        """
        Update which disciplines are active and recalculate totals/ranks.

        Args:
            discipline_codes: Set of discipline codes to activate
        """
        self.competition.set_active_disciplines(discipline_codes)

        # Recalculate all totals and ranks
        for startnumber in self.competition.participants:
            self.recalculate_participant(startnumber)
        self.recalculate_all_ranks()

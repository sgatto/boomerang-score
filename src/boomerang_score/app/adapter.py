"""Adapter to bridge new models/services with existing GUI code."""

class LegacyDataAdapter:
    """
    Adapter that makes Competition/Participant work like the old self.data dict.

    This allows minimal changes to existing GUI code while using new domain models.
    """

    def __init__(self, competition, service):
        """
        Args:
            competition: Competition instance
            service: CompetitionService instance
        """
        self.competition = competition
        self.service = service

    def __getitem__(self, participant_id):
        """Get participant data as a dict (like old self.data[iid])."""
        participant = self.competition.get_participant(participant_id)
        if not participant:
            raise KeyError(participant_id)

        # Convert Participant to dict format expected by GUI
        result = {
            "name": participant.name,
            "startnumber": participant.startnumber,
            "total": participant.total_points,
            "overall_rank": participant.overall_rank,
        }

        # Add discipline fields
        for disc_code in participant.disciplines.keys():
            result[f"{disc_code}_res"] = participant.get_result(disc_code)
            result[f"{disc_code}_pts"] = participant.get_points(disc_code)
            result[f"{disc_code}_rank"] = participant.get_rank(disc_code)

        return result

    def __setitem__(self, participant_id, row_dict):
        """Set participant data from dict (not typically used, prefer service methods)."""
        # This is mainly for backward compatibility if needed
        pass

    def __contains__(self, participant_id):
        """Check if participant exists."""
        return participant_id in self.competition.participants

    def __iter__(self):
        """Iterate over participant IDs."""
        return iter(self.competition.participants)

    def keys(self):
        """Get all participant IDs."""
        return self.competition.participants.keys()

    def values(self):
        """Get all participants as dicts."""
        return [self[pid] for pid in self.keys()]

    def items(self):
        """Get (participant_id, dict) pairs."""
        return [(pid, self[pid]) for pid in self.keys()]

    def get(self, participant_id, default=None):
        """Get participant dict or default."""
        try:
            return self[participant_id]
        except KeyError:
            return default

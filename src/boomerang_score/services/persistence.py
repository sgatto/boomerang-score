"""JSON persistence for Competition data."""

import json

from boomerang_score.core.models import Competition, DisciplineResult, Participant


class CompetitionRepository:
    """Saves and loads Competition instances as JSON .bscore files."""

    FORMAT_VERSION = 1

    def save(self, competition: Competition, path: str) -> None:
        """Serialize competition to a JSON file at the given path."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._serialize(competition), f, indent=2, ensure_ascii=False)

    def load(self, path: str) -> Competition:
        """Deserialize a competition from a JSON file."""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Could not read file: {e}")
        return self._deserialize(data)

    def _serialize(self, competition: Competition) -> dict:
        participants = {}
        for startnr, p in competition.participants.items():
            disciplines = {
                code: {"result": dr.result, "points": dr.points, "rank": dr.rank}
                for code, dr in p.disciplines.items()
            }
            participants[str(startnr)] = {
                "name": p.name,
                "startnumber": p.startnumber,
                "total_points": p.total_points,
                "overall_rank": p.overall_rank,
                "disciplines": disciplines,
            }
        return {
            "version": self.FORMAT_VERSION,
            "title": competition.title,
            "logo_path": competition.logo_path,
            "active_disciplines": sorted(competition.active_disciplines),
            "participants": participants,
        }

    def _deserialize(self, data: dict) -> Competition:
        competition = Competition(
            title=data.get("title", "My Competition"),
            logo_path=data.get("logo_path"),
        )
        competition.set_active_disciplines(set(data.get("active_disciplines", [])))

        for startnr_str, p_data in data.get("participants", {}).items():
            participant = Participant(
                name=p_data["name"],
                startnumber=int(startnr_str),
            )
            participant.total_points = p_data.get("total_points")
            participant.overall_rank = p_data.get("overall_rank")
            for code, dr_data in p_data.get("disciplines", {}).items():
                participant.disciplines[code] = DisciplineResult(
                    result=dr_data.get("result"),
                    points=dr_data.get("points"),
                    rank=dr_data.get("rank"),
                )
            competition.add_participant(participant)

        return competition

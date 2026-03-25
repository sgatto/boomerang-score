"""Core domain models and scoring logic."""

from .models import Participant, Competition, DisciplineResult
from .scorer import (
    compute_competition_ranks,
    ACC, AUS, MTA, END, FC, TC, TIMED
)

__all__ = [
    "Participant",
    "Competition",
    "DisciplineResult",
    "compute_competition_ranks",
    "ACC", "AUS", "MTA", "END", "FC", "TC", "TIMED"
]

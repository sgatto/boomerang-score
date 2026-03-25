"""Core domain models and scoring logic."""

from .models import Participant, Competition, DisciplineResult
from .scorer import (
    compute_competition_ranks,
    ACC, AUS, MTA, END, FC, TC, TIMED
)
from .constants import (
    DISC_CODE_ACC, DISC_CODE_AUS, DISC_CODE_MTA, DISC_CODE_END,
    DISC_CODE_FC, DISC_CODE_TC, DISC_CODE_TIMED,
    DISC_LABEL_ACC, DISC_LABEL_AUS, DISC_LABEL_MTA, DISC_LABEL_END,
    DISC_LABEL_FC, DISC_LABEL_TC, DISC_LABEL_TIMED,
    ALL_DISCIPLINE_CODES, ALL_DISCIPLINE_LABELS
)

__all__ = [
    "Participant",
    "Competition",
    "DisciplineResult",
    "compute_competition_ranks",
    "ACC", "AUS", "MTA", "END", "FC", "TC", "TIMED",
    "DISC_CODE_ACC", "DISC_CODE_AUS", "DISC_CODE_MTA", "DISC_CODE_END",
    "DISC_CODE_FC", "DISC_CODE_TC", "DISC_CODE_TIMED",
    "DISC_LABEL_ACC", "DISC_LABEL_AUS", "DISC_LABEL_MTA", "DISC_LABEL_END",
    "DISC_LABEL_FC", "DISC_LABEL_TC", "DISC_LABEL_TIMED",
    "ALL_DISCIPLINE_CODES", "ALL_DISCIPLINE_LABELS"
]

"""Constants for discipline codes and labels.

These constants should be used throughout the codebase instead of magic strings.
"""

# Discipline codes (lowercase) - used as dict keys, internal identifiers
DISC_CODE_ACC = "acc"
DISC_CODE_AUS = "aus"
DISC_CODE_MTA = "mta"
DISC_CODE_END = "end"
DISC_CODE_FC = "fc"
DISC_CODE_TC = "tc"
DISC_CODE_TIMED = "timed"
DISC_CODE_TAPIR = "tapir"

# Discipline labels (uppercase) - used for display only
DISC_LABEL_ACC = "ACC"
DISC_LABEL_AUS = "AUS"
DISC_LABEL_MTA = "MTA"
DISC_LABEL_END = "END"
DISC_LABEL_FC = "FC"
DISC_LABEL_TC = "TC"
DISC_LABEL_TIMED = "TIMED"
DISC_LABEL_TAPIR = "TAPIR"

# All discipline codes (for iteration)
ALL_DISCIPLINE_CODES = [
    DISC_CODE_ACC,
    DISC_CODE_AUS,
    DISC_CODE_MTA,
    DISC_CODE_END,
    DISC_CODE_FC,
    DISC_CODE_TC,
    DISC_CODE_TIMED,
    DISC_CODE_TAPIR,
]

# All discipline labels (for display)
ALL_DISCIPLINE_LABELS = [
    DISC_LABEL_ACC,
    DISC_LABEL_AUS,
    DISC_LABEL_MTA,
    DISC_LABEL_END,
    DISC_LABEL_FC,
    DISC_LABEL_TC,
    DISC_LABEL_TIMED,
    DISC_LABEL_TAPIR,
]

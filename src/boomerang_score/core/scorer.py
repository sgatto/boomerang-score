import math
from .constants import (
    DISC_CODE_ACC,
    DISC_CODE_AUS,
    DISC_CODE_AUS40,
    DISC_CODE_MTA,
    DISC_CODE_END,
    DISC_CODE_END3,
    DISC_CODE_FC,
    DISC_CODE_TC,
    DISC_CODE_TC50,
    DISC_CODE_TIMED,
    DISC_CODE_TAPIR,
    DISC_LABEL_ACC,
    DISC_LABEL_AUS,
    DISC_LABEL_AUS40,
    DISC_LABEL_MTA,
    DISC_LABEL_END,
    DISC_LABEL_END3,
    DISC_LABEL_FC,
    DISC_LABEL_TC,
    DISC_LABEL_TC50,
    DISC_LABEL_TIMED,
    DISC_LABEL_TAPIR,
)


def compute_competition_ranks(items):
    """
    Standard competition ranking (1, 1, 3, 4, 4, 6, ...)
    items: List[(iid, value)], higher value = better
    Returns: dict[iid] -> rank
    """
    norm = []
    for iid, val in items:
        try:
            v = float(val)
        except (TypeError, ValueError):
            v = float("-inf")
        norm.append((iid, v))
    norm.sort(key=lambda x: x[1], reverse=True)

    ranks = {}
    prev_val = None
    rank = 0
    count = 0
    for iid, v in norm:
        count += 1
        if prev_val is None or v != prev_val:
            rank = count
            prev_val = v
        ranks[iid] = rank
    return ranks


class Discipline:
    def __init__(self, code, label, default_active, points_func):
        self.code = code  # 'acc'
        self.label = label  # 'ACC'
        self.default_active = default_active
        self.points_func = points_func


def safe_div(numer, denom):
    try:
        denom = float(denom)
        if denom == 0:
            return 0.0
        return float(numer) / denom
    except (TypeError, ValueError):
        return 0.0


def _points_100(result):
    max_score_100 = 100
    if result < 0:
        points = -200
    elif result < max_score_100:
        points = 500 * math.log10(1 + 99 * (float(result) / max_score_100))
    else:
        points = 1000
    return points


def _points_80(result):
    max_score_80 = 80
    if result < 0:
        points = -200
    else:
        points = 500 * math.log10(1 + 99 * (float(result) / max_score_80))
    return points


def _points_80max(result):
    max_score_80 = 80
    if result < 0:
        points = -200
    elif result < max_score_80:
        points = 500 * math.log10(1 + 99 * (float(result) / max_score_80))
    else:
        points = 1000
    return points


def _points_50max(result):
    max_score_50 = 50
    if result < 0:
        points = -200
    elif result < max_score_50:
        points = 500 * math.log10(1 + 99 * (float(result) / max_score_50))
    else:
        points = 1000
    return points


def _points_50(result):
    max_score_50 = 50
    if result < 0:
        points = -200
    else :
        points = 500 * math.log10(1 + 99 * (float(result) / max_score_50))
    return points


def _points_fc(result):
    _max_time = 60.0
    _min_time = 15.00
    _laps = 5
    if result >= 75: 
        #complete round maxtime cut off
        points = 500 * math.log10(1 + 99 * (_min_time / 75.00))
    elif result >= 5: 
        #complete round
        points = 500 * math.log10(1 + 99 * (_min_time / float(result)))
    elif result >= 0:
         #non complete round, points scaled by laps completed
         #for non complete rounds the score is the number of the catches
         points = 500 * math.log10(1 + 99 * (_min_time / _max_time *(float(result) / _laps)))
    else:
        points = -200
    return points


def _points_timed(result):
    _max_time = 60.0
    if result == 0:
        points = 0
    elif result == 1:
        points = 387.26
    elif result == 2:
        points = 518.71
    elif result == 3:
        points = 600.01
    elif result == 4:
        points = 659.03
    elif result >= 75:
        points = 659.03
    elif result > 5:
        points = 500 * math.log10(1 + 99 * safe_div(15.00, result))
    else:
        points = -200
    return points


def _points_tapir(result):
    _max_time = 300.0
    _min_time = 90.00
    _laps = 0.85
    _maxtime_cut_off = float(_max_time*_laps/(_laps-0.01))
    if result >= _maxtime_cut_off:
        #complete round maxtime cut off
        points = 500 * math.log10(1 + 99 * (_min_time / _maxtime_cut_off))
    elif result >= 0.85:
        #complete round
        points = 500 * math.log10(1 + 99 * (_min_time / float(result)))
    elif result > 0:
        #non complete round, points scaled by laps completed
        #each ACC point is 0.01 points
        #each TC is 0.05 points related to the acc points for each TC
        #0.05 points for each FC
        #so total for 4 Fast Catches is 0.8 points
        points = 500 * math.log10(1 + 99 * (_min_time / _max_time *(float(result) / _laps)))
    else:
        points = -200
    return points


ACC = Discipline(DISC_CODE_ACC, DISC_LABEL_ACC, True, lambda e: _points_100(float(e)))
AUS = Discipline(DISC_CODE_AUS, DISC_LABEL_AUS, True, lambda e: _points_100(float(e)))
AUS40 = Discipline(DISC_CODE_AUS40, DISC_LABEL_AUS40, False, lambda e: _points_80max(float(e)))
MTA = Discipline(DISC_CODE_MTA, DISC_LABEL_MTA, True, lambda e: _points_50max(float(e)))
END = Discipline(DISC_CODE_END, DISC_LABEL_END, True, lambda e: _points_80(float(e)))
END3 = Discipline(DISC_CODE_END3, DISC_LABEL_END3, False, lambda e: _points_50(float(e)))
FC = Discipline(DISC_CODE_FC, DISC_LABEL_FC, True, lambda e: _points_fc(float(e)))
TC = Discipline(DISC_CODE_TC, DISC_LABEL_TC, True, lambda e: _points_100(float(e)))
TC50 = Discipline(DISC_CODE_TC50, DISC_LABEL_TC50, False, lambda e: _points_50max(float(e)))
TIMED = Discipline(
    DISC_CODE_TIMED, DISC_LABEL_TIMED, False, lambda e: _points_timed(float(e))
)
TAPIR = Discipline(
    DISC_CODE_TAPIR, DISC_LABEL_TAPIR, False, lambda e: _points_tapir(float(e))
)

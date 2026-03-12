import math


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
        self.code = code      # 'acc'
        self.label = label    # 'ACC'
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
    elif result < 100:
       points = 500 * math.log10( 1 + 99 * (float(result) / max_score_100))
    else:
       points = 1000
    return points


def _points_80(result):
    max_score_80 = 80
    if result < 0:
       points = -200
    else:
       points = 500 * math.log10( 1 + 99 * (float(result) / max_score_80))
    return points


def _points_50(result):
    max_score_50 = 50
    if result < 0:
       points = -200
    elif result < max_score_50:
       points = 500 * math.log10( 1 + 99 * (float(result) / max_score_50))
    else:
       points = 1000
    return points


def _points_fc(result):
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
    elif result >= 5:
       points = 500 * math.log10( 1 + 99 * ( 15.00 / float(result)))
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
       points = 500 * math.log10( 1 + 99 * ( 15.00 / float(result)))
    else:
       points = -200
    return points


DISCIPLINES = [
    Discipline("acc", "ACC",   True,  lambda e: _points_100(float(e)) ),
    Discipline("aus", "AUS",   True,  lambda e: _points_100(float(e)) ),
    Discipline("mta", "MTA",   True,  lambda e: _points_50(float(e)) ),
    Discipline("end", "END",   True,  lambda e: _points_80(float(e)) ),
    Discipline("fc",  "FC",    True,  lambda e: _points_fc(float(e)) ),
    Discipline("tc",  "TC",    True,  lambda e: _points_100(float(e)) ),
    Discipline("timed","TIMED",False, lambda e: _points_timed(float(e)) ),
]

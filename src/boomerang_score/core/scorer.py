import math


def compute_competition_ranks(items):
    """
    Standard-Wettbewerbsranking (1, 1, 3, 4, 4, 6, ...)
    items: Liste[(iid, value)], höherer Wert = besser
    Rückgabe: dict[iid] -> rank
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


def _points_100(_erg):
    max_score_100 = 100
    if _erg < 0:
       _loc_points = -200
    elif _erg < 100:
       _loc_points = 500 * math.log10( 1 + 99 * (float(_erg) / max_score_100))
    else:
       _loc_points = 1000
    return _loc_points


def _points_80(_erg):
    max_score_80 = 80
    if _erg < 0:
       _loc_points = -200
    else:
       _loc_points = 500 * math.log10( 1 + 99 * (float(_erg) / max_score_80))
    return _loc_points


def _points_50(_erg):
    max_score_50 = 50
    if _erg < 0:
       _loc_points = -200
    elif _erg < max_score_50:
       _loc_points = 500 * math.log10( 1 + 99 * (float(_erg) / max_score_50))
    else:
       _loc_points = 1000
    return _loc_points


def _points_fc(_erg):
    _max_time = 60.0
    if _erg == 0:
       _loc_points = 0
    elif _erg == 1:
       _loc_points = 387.26
    elif _erg == 2:
       _loc_points = 518.71
    elif _erg == 3:
       _loc_points = 600.01
    elif _erg == 4:
       _loc_points = 659.03
    elif _erg >= 75:
       _loc_points = 659.03
    elif _erg >= 5:
       _loc_points = 500 * math.log10( 1 + 99 * ( 15.00 / float(_erg)))
    else:
       _loc_points = -200
    return _loc_points


def _points_timed(_erg):
    _max_time = 60.0
    if _erg == 0:
       _loc_points = 0
    elif _erg == 1:
       _loc_points = 387.26
    elif _erg == 2:
       _loc_points = 518.71
    elif _erg == 3:
       _loc_points = 600.01
    elif _erg == 4:
       _loc_points = 659.03
    elif _erg >= 75:
       _loc_points = 659.03
    elif _erg > 5:
       _loc_points = 500 * math.log10( 1 + 99 * ( 15.00 / float(_erg)))
    else:
       _loc_points = -200
    return _loc_points


DISCIPLINES = [
    Discipline("acc", "ACC",   True,  lambda e: _points_100(float(e)) ),
    Discipline("aus", "AUS",   True,  lambda e: _points_100(float(e)) ),
    Discipline("mta", "MTA",   True,  lambda e: _points_50(float(e)) ),
    Discipline("end", "END",   True,  lambda e: _points_80(float(e)) ),
    Discipline("fc",  "FC",    True,  lambda e: _points_fc(float(e)) ),
    Discipline("tc",  "TC",    True,  lambda e: _points_100(float(e)) ),
    Discipline("timed","TIMED",False, lambda e: _points_timed(float(e)) ),
]

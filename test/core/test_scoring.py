import math


def points_100(result):
    max_score_100 = 100
    if result < 0:
       points = -200
    elif result < 100:
       points = 500 * math.log10( 1 + 99 * (float(result) / max_score_100))
    else:
       points = 1000
    return points


def test_accuracy_score_of_100_gives_1000_points():
    assert points_100(100) == 1000


def test_tapir_points():
    from boomerang_score.core.scorer import _points_tapir
    assert _points_tapir(10) == 30.0
    assert _points_tapir("5") == 15.0
    assert _points_tapir("abc") == 0.0


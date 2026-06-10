import pytest
import math
from boomerang_score.core.scorer import (
    compute_competition_ranks,
    safe_div,
    _points_100,
    _points_80,
    _points_80max,
    _points_50max,
    _points_50,
    _points_fc,
    _points_timed,
    _points_tapir,
    ACC, AUS, AUS40, MTA, END, END3, FC, TC, TC50, TIMED, TAPIR,
    Discipline
)

def test_compute_competition_ranks():
    # Standard competition ranking: (1, 1, 3, 4, 4, 6, ...)
    items = [("p1", 100), ("p2", 100), ("p3", 90), ("p4", 80), ("p5", 80), ("p6", 70)]
    ranks = compute_competition_ranks(items)
    assert ranks == {"p1": 1, "p2": 1, "p3": 3, "p4": 4, "p5": 4, "p6": 6}

    # Empty list
    assert compute_competition_ranks([]) == {}

    # Invalid values
    items = [("p1", 100), ("p2", "invalid"), ("p3", 90)]
    # "invalid" becomes -inf
    ranks = compute_competition_ranks(items)
    assert ranks == {"p1": 1, "p3": 2, "p2": 3}

    # All same scores
    items = [("p1", 50), ("p2", 50)]
    assert compute_competition_ranks(items) == {"p1": 1, "p2": 1}

def test_safe_div():
    assert safe_div(10, 2) == 5.0
    assert safe_div(10, 0) == 0.0
    assert safe_div(10, "2") == 5.0
    assert safe_div("10", 2) == 5.0
    assert safe_div(10, "abc") == 0.0
    assert safe_div("abc", 2) == 0.0

@pytest.mark.parametrize("score, expected", [
    (100, 1000),
    (0, 0),
    (-1, -200),
    (50, 500 * math.log10(1 + 99 * 0.5)),
    (150, 1000),
    (-1, -200),
])
def test_points_100(score, expected):
    assert _points_100(score) == pytest.approx(expected)

@pytest.mark.parametrize("score, expected", [
    (0, 0),
    (-1, -200),
    (40, 500 * math.log10(1 + 99 * 0.5)),
    (80, 1000),
    (160, 500 * math.log10(1 + 99 * 2)), # No cap for _points_80
    (-1, -200),
])
def test_points_80(score, expected):
    assert _points_80(score) == pytest.approx(expected)

@pytest.mark.parametrize("score, expected", [
    (80, 1000),
    (100, 1000), # Cap for _points_80max
    (40, 500 * math.log10(1 + 99 * 0.5)),
])
def test_points_80max(score, expected):
    assert _points_80max(score) == pytest.approx(expected)

@pytest.mark.parametrize("score, expected", [
    (50, 1000),
    (60, 1000), # Cap
    (25, 500 * math.log10(1 + 99 * 0.5)),
    (-1, -200),
])
def test_points_50max(score, expected):
    assert _points_50max(score) == pytest.approx(expected)

@pytest.mark.parametrize("score, expected", [
    (0, 0),
    (50, 1000),
    (100, 500 * math.log10(1 + 99 * 2)), # No cap
    (-1, -200),
])
def test_points_50(score, expected):
    assert _points_50(score) == pytest.approx(expected)

@pytest.mark.parametrize("score, expected", [
    (75, 500 * math.log10(1 + 99 * (15.0/75.0))), # complete round maxtime cut off
    (80, 500 * math.log10(1 + 99 * (15.0/75.0))),
    (5, 1234.98), # 15/5 = 3. 1 + 99*3 = 298. 500*log10(298) ~ 1237? Wait, calc again.
    (15, 1000), # 15/15 = 1. 1 + 99*1 = 100. 500*log10(100) = 500*2 = 1000. Correct.
    (4, 500 * math.log10(1 + 99 * (15.0 / 60.0 * (4.0 / 5.0)))), # non complete round
    (0, 0),
    (-1, -200),
    )
])
def test_points_fc(score, expected):
    # result 5 calculation: 1 + 99 * (15/5) = 1 + 99*3 = 298. 500 * log10(298) = 500 * 2.4742 = 1237.1
    if score == 5:
        expected = 500 * math.log10(298)
    assert _points_fc(score) == pytest.approx(expected)

@pytest.mark.parametrize("score, expected", [
    (0, 0),
    (1, 387.26),
    (2, 518.71),
    (3, 600.01),
    (4, 659.03),
    (75, 659.03),
    (80, 659.03),
    (15, 1000), # 500 * log10(1 + 99 * (15/15)) = 1000
    (10, 500 * math.log10(1 + 99 * (15.0 / 10.0))),
    (5, -200),
])
def test_points_timed(score, expected):
    assert _points_timed(score) == pytest.approx(expected)

@pytest.mark.parametrize("score, expected", [
    (300, 500 * math.log10(1 + 99 * (90.0/300.0))), 
    (310, 500 * math.log10(1 + 99 * (90.0 / 303.57142857142856))),
    (90, 1000), 
    (1, 500 * math.log10(1 + 99 * (90.0 / 1.0))),
    (0.5, 500 * math.log10(1 + 99 * (90.0 / 300.0 * (0.5 / 0.85)))),
    (0, -200),
])
def test_points_tapir(score, expected):
    # _maxtime_cut_off = 300 * 0.85 / (0.85 - 0.01) = 255 / 0.84 = 303.5714...
    # if score >= 303.5714... it uses 303.5714...
    if score == 310:
        expected = 500 * math.log10(1 + 99 * (90.0 / 303.57142857142856))
    elif score == 300:
        expected = 500 * math.log10(1 + 99 * (90.0 / 300.0))
    assert _points_tapir(score) == pytest.approx(expected)

def test_disciplines():
    assert ACC.code == "acc"
    assert ACC.label == "ACC"
    assert ACC.default_active is True
    assert ACC.points_func(100) == 1000

    assert AUS40.code == "aus40"
    assert AUS40.default_active is False
    assert AUS40.points_func(80) == 1000

    assert FC.points_func(15) == 1000
    assert TIMED.points_func(15) == 1000
    assert TAPIR.points_func(90) == 1000

def test_discipline_class():
    d = Discipline("test", "TEST", True, lambda x: x * 2)
    assert d.code == "test"
    assert d.label == "TEST"
    assert d.default_active is True
    assert d.points_func(10) == 20

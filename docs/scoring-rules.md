---
layout: default
title: Scoring Rules
---

# Scoring Rules

This page explains how Boomerang Score calculates points for each of the 8 discipline events.

## Overview

Each participant competes in up to 8 disciplines. Points are awarded based on performance in each event using a **logarithmic scale**: small improvements at the low end of the scale yield more points than the same improvement at the high end. Final rankings are computed by summing points across active disciplines.

The general formula used is:

```
points = 500 * log10(1 + 99 * (result / max_result))
```

This gives 0 points for a result of 0 and 1000 points for a perfect result, with diminishing returns near the top.

## The 8 Disciplines

### 1. Accuracy (ACC)

**How it works:** Throw boomerang at targets; score is a percentage (0–100) based on how close each throw lands to the center.

**Scoring:** Uses `_points_100` — logarithmic scale with max input 100.
- 0 → 0 pts, 100 → 1000 pts
- Negative input → −200 pts (penalty)

### 2. Australian Round (AUS)

**How it works:** Throw to maximize distance while returning to thrower. Measured as a score out of 100.

**Scoring:** Uses `_points_100` — same logarithmic scale as ACC.
- 0 → 0 pts, 100 → 1000 pts

### 3. Maximum Time Aloft (MTA)

**How it works:** Single throw for maximum flight time. Scored as a value out of 50 seconds.

**Scoring:** Uses `_points_50` — logarithmic scale with max input 50.
- 0 → 0 pts, 50 → 1000 pts
- Values above 50 are capped at 1000 pts

### 4. Endurance (END)

**How it works:** Throw repeatedly; score is number of catches. Scored as a value out of 80.

**Scoring:** Uses `_points_80` — logarithmic scale with max input 80.
- 0 → 0 pts, 80 → ~1000 pts (no upper cap)

### 5. Fast Catch (FC)

**How it works:** Catch as many throws as possible within a time limit.

**Scoring:** Uses a special lookup/formula (`_points_fc`):
- 0 catches → 0 pts
- 1 catch → 387.26 pts
- 2 catches → 518.71 pts
- 3 catches → 600.01 pts
- 4 catches → 659.03 pts
- 5+ catches → `500 * log10(1 + 99 * (15 / result))` (inverted: fewer catches = more time = better)
- ≥75 catches → capped at 659.03 pts

### 6. Trick Catch (TC)

**How it works:** Execute trick catches (behind back, one-handed, etc.). Scored as a percentage out of 100.

**Scoring:** Uses `_points_100` — same logarithmic scale as ACC.
- 0 → 0 pts, 100 → 1000 pts

### 7. Timed Catch (TIMED)

**How it works:** Catch boomerang within a time window. Scored as number of successful catches.

**Scoring:** Uses `_points_timed` — same lookup table as FC for 0–4 catches, then logarithmic for 5+.
- 0 catches → 0 pts
- 1–4 catches → fixed values (387.26 / 518.71 / 600.01 / 659.03)
- 5+ catches → `500 * log10(1 + 99 * (15 / result))`
- ≥75 catches → capped at 659.03 pts

### 8. Tapir (TAPIR)

**How it works:** Specialized combined event.

**Scoring:** Linear: `points = result * 3`

## Computing Competition Rankings

1. **Per-discipline scoring** — Each participant's raw result is passed through the discipline's `points_func` to get points.

2. **Ranking within discipline** — Participants are ranked 1st, 2nd, 3rd, etc. by points. Ties receive the same rank (standard competition ranking: 1, 1, 3, ...).

3. **Aggregation** — Points from all **active** disciplines are summed into `total_points`.

4. **Final rankings** — Participants ranked by `total_points` descending.

## Modifying Scoring Rules

All scoring logic lives in `src/boomerang_score/core/scorer.py`. To change how a discipline is scored:

1. Open `scorer.py`
2. Find or add the scoring function for that discipline (e.g., `_points_100()`)
3. Modify the formula
4. Add or update tests in `test/core/test_scoring.py`
5. Run tests: `uv run pytest test/core/test_scoring.py -v`

Example — the accuracy scoring function:

```python
def _points_100(result):
    max_score_100 = 100
    if result < 0:
        points = -200
    elif result < 100:
        points = 500 * math.log10(1 + 99 * (float(result) / max_score_100))
    else:
        points = 1000
    return points
```

Changes take effect immediately in the GUI after reload.

## Points Distribution

Approximate points range per discipline:

| Discipline | Formula     | Max Input | Max Points |
|---|---|---|---|
| ACC        | log scale   | 100       | 1000       |
| AUS        | log scale   | 100       | 1000       |
| MTA        | log scale   | 50        | 1000       |
| END        | log scale   | 80        | ~1000+     |
| FC         | lookup+log  | —         | 659        |
| TC         | log scale   | 100       | 1000       |
| TIMED      | lookup+log  | —         | 659        |
| TAPIR      | linear ×3   | —         | unbounded  |

## Handicapping

Some tournaments use handicaps to level the playing field. If needed:

1. **Add to `DisciplineResult`** — Store handicap as a field
2. **Apply in scorer** — Adjust final points: `points - handicap_adjustment`
3. **Update GUI** — Show handicap in table

This would require changes to `core/models.py` and `core/scorer.py`.

## Further Reading

- [Architecture](architecture.md) — Understand how scoring logic is structured
- See `src/boomerang_score/core/scorer.py` for implementation details
- Test examples in `test/core/test_scoring.py`

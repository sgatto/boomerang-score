---
layout: default
title: Scoring Rules
---

# Scoring Rules

This page explains how Boomerang Score calculates points for each of the 8 discipline events.

## Overview

Each participant competes in up to 8 disciplines. Points are awarded based on performance in each event. Final rankings are computed by summing points across disciplines.

## The 8 Disciplines

### 1. Accuracy (ACC)

**How it works:** Throw boomerang at targets; score is sum of distances (in cm) from center of each target.

**Scoring:**
- Lower distance = better
- Points awarded inversely: `points = 100 - (distance / max_distance) * 100`

### 2. Australian Round (AUS)

**How it works:** Throw to maximize distance while returning to thrower. Measured in meters.

**Scoring:**
- Higher distance = better
- Points: `distance (m) * 10`

### 3. Maximum Time Aloft (MTA)

**How it works:** Single throw for maximum flight time. Measured in seconds.

**Scoring:**
- Higher time = better
- Points: `flight_time (s) * 10`

### 4. Endurance (END)

**How it works:** Throw repeatedly, score number of catches before dropping or time limit.

**Scoring:**
- Higher catches = better
- Points: `num_catches * 5`

### 5. Fast Catch (FC)

**How it works:** Catch as many throws as possible within time limit (e.g., 60 seconds).

**Scoring:**
- Higher catches = better
- Points: `num_catches * 3`

### 6. Trick Catch (TC)

**How it works:** Execute trick catches (behind back, one-handed, etc.). Scored by difficulty and count.

**Scoring:**
- Points awarded per trick level and count
- Base: `difficulty_level * 2`, multiplied by count

### 7. Timed Catch (TIMED)

**How it works:** Catch boomerang within time window (e.g., 20 seconds).

**Scoring:**
- Success = catches within window
- Points: `num_successful_catches * 10`

### 8. Tapir (TAPIR)

**How it works:** Specialized event. Usually distance + accuracy combined.

**Scoring:**
- Points: `(distance * 2) + (accuracy_bonus)`

## Computing Competition Rankings

1. **Per-discipline scoring** — Each participant receives points for their performance in that discipline.

2. **Ranking within discipline** — Participants are ranked 1st, 2nd, 3rd, etc. by points. Ties are handled by awarding the same rank.

3. **Aggregation** — Points from all disciplines are summed. Participant with highest total wins.

4. **Final rankings** — Displayed in descending order of total points.

## Modifying Scoring Rules

All scoring logic lives in `src/boomerang_score/core/scorer.py`. To change how a discipline is scored:

1. Open `scorer.py`
2. Find the scoring function for that discipline (e.g., `score_accuracy()`)
3. Modify the formula
4. Add or update tests in `test/core/test_scoring.py`
5. Run tests: `uv run pytest test/core/test_scoring.py -v`

Example:

```python
def score_accuracy(distances, catches):
    """Accuracy scoring: lower distance is better."""
    total_distance = sum(distances)
    max_possible = 1000.0
    points = max(0, 100 - (total_distance / max_possible) * 100)
    return DisciplineResult(points=points, raw_value=total_distance)
```

Changes take effect immediately in the GUI after reload.

## Points Distribution

Typical points distribution (rough guide):

| Discipline | Min | Max | Notes |
|---|---|---|---|
| ACC | 0 | 100 | Accuracy-based |
| AUS | 0 | 150+ | Distance-based |
| MTA | 0 | 200+ | Time-based |
| END | 0 | 100+ | Count-based |
| FC | 0 | 80+ | Count-based |
| TC | 0 | 100+ | Trick-based |
| TIMED | 0 | 100+ | Count-based |
| TAPIR | 0 | 150+ | Combined |

Maximum total: ~950 points (varies by event rules).

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

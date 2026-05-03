---
layout: default
title: API Reference
---

# API Reference

Core module documentation for programmers building on or extending Boomerang Score.

## Core Module

### `boomerang_score.core.models`

Data classes representing tournament state. Immutable where possible.

#### `Competition`

Tournament container.

```python
class Competition:
    name: str
    participants: list[Participant]
    
    def add_participant(p: Participant) -> None
    def remove_participant(number: int) -> None
    def get_participant(number: int) -> Participant | None
    def get_all_scores(discipline_code: str) -> dict[int, float]
```

#### `Participant`

Person in the tournament.

```python
class Participant:
    name: str
    number: int
    results: dict[str, DisciplineResult]  # discipline_code -> result
    
    def get_score(discipline_code: str) -> float | None
    def set_score(discipline_code: str, result: DisciplineResult) -> None
```

#### `DisciplineResult`

Result for one discipline.

```python
class DisciplineResult:
    points: float           # Computed points for ranking
    raw_value: float | int  # Raw measurement (distance, time, count, etc.)
    timestamp: datetime     # When score was recorded
```

---

### `boomerang_score.core.scorer`

Scoring functions. All pure functions with no side effects.

#### `compute_competition_ranks(competition: Competition) -> dict[int, int]`

Compute ranking (1st, 2nd, 3rd, etc.) for all participants based on total points across disciplines.

**Returns:** `{ participant_number: rank }`

```python
competition = Competition(name="Tournament")
# ... add participants with scores ...
ranks = compute_competition_ranks(competition)
print(ranks[1])  # Rank of participant #1
```

#### `score_accuracy(distances: list[float], catches: int) -> DisciplineResult`

Accuracy (ACC) discipline: lower distance to center is better.

**Parameters:**
- `distances`: List of distances (cm) from center for each throw
- `catches`: Number of successful catches

**Returns:** `DisciplineResult` with points and raw distance sum

#### `score_australian_round(distance: float) -> DisciplineResult`

Australian Round (AUS): maximize distance while returning.

**Parameters:**
- `distance`: Flight distance in meters

**Returns:** `DisciplineResult` with points

#### `score_mta(flight_time: float) -> DisciplineResult`

Maximum Time Aloft (MTA): maximize flight time.

**Parameters:**
- `flight_time`: Seconds in air

**Returns:** `DisciplineResult` with points

#### `score_endurance(catches: int) -> DisciplineResult`

Endurance (END): maximum catches before drop.

**Parameters:**
- `catches`: Number of successful catches

**Returns:** `DisciplineResult` with points

#### `score_fast_catch(catches: int) -> DisciplineResult`

Fast Catch (FC): catches within time limit.

**Parameters:**
- `catches`: Number of catches in window

**Returns:** `DisciplineResult` with points

#### `score_trick_catch(tricks: int, difficulty: int = 1) -> DisciplineResult`

Trick Catch (TC): trick difficulty and count.

**Parameters:**
- `tricks`: Number of trick catches
- `difficulty`: Average difficulty level (1-5)

**Returns:** `DisciplineResult` with points

#### `score_timed_catch(catches: int) -> DisciplineResult`

Timed Catch (TIMED): catches within time window.

**Parameters:**
- `catches`: Number within window

**Returns:** `DisciplineResult` with points

#### `score_tapir(distance: float, accuracy_bonus: float = 0) -> DisciplineResult`

Tapir (TAPIR): combined distance + accuracy.

**Parameters:**
- `distance`: Flight distance in meters
- `accuracy_bonus`: Accuracy bonus points (0-100)

**Returns:** `DisciplineResult` with points

---

### `boomerang_score.core.constants`

Discipline codes and metadata.

```python
from boomerang_score.core.constants import (
    DISC_CODE_ACC,      # "ACC"
    DISC_CODE_AUS,      # "AUS"
    DISC_CODE_MTA,      # "MTA"
    DISC_CODE_END,      # "END"
    DISC_CODE_FC,       # "FC"
    DISC_CODE_TC,       # "TC"
    DISC_CODE_TIMED,    # "TIMED"
    DISC_CODE_TAPIR,    # "TAPIR"
    ALL_DISCIPLINES,    # list of all 8 codes
)

DISCIPLINE_LABELS = {
    "ACC": "Accuracy",
    "AUS": "Australian Round",
    # ...
}
```

---

## Services Module

### `boomerang_score.services.competition_service`

High-level tournament operations. Orchestrates core + persistence.

#### `CompetitionService`

```python
class CompetitionService:
    def __init__(repository: CompetitionRepository)
    
    def add_participant(
        name: str,
        number: int,
        scores: dict[str, float] = None
    ) -> Participant
    
    def remove_participant(number: int) -> None
    
    def update_score(
        number: int,
        discipline_code: str,
        raw_value: float
    ) -> Participant
    
    def get_competition() -> Competition
    
    def save_competition(filepath: str) -> None
    
    def load_competition(filepath: str) -> Competition
```

**Example:**

```python
from boomerang_score.services import CompetitionService, CompetitionRepository
from boomerang_score.core.constants import DISC_CODE_ACC, DISC_CODE_AUS

repo = CompetitionRepository()
service = CompetitionService(repo)

# Add participant
p = service.add_participant(
    "John Doe",
    1,
    {DISC_CODE_ACC: 80.5, DISC_CODE_AUS: 95.0}
)

# Update score
service.update_score(1, DISC_CODE_ACC, 85.0)

# Save
service.save_competition("tournament.json")
```

---

### `boomerang_score.services.export_service`

Document generation.

#### `export_to_pdf(competition: Competition, filepath: str) -> str`

Generate PDF report of competition results.

**Returns:** Path to created file

```python
from boomerang_score.services import export_to_pdf

path = export_to_pdf(competition, "results.pdf")
print(f"Exported to {path}")
```

#### `export_to_word(competition: Competition, filepath: str) -> str`

Generate Word (.docx) report.

**Returns:** Path to created file

```python
from boomerang_score.services import export_to_word

path = export_to_word(competition, "results.docx")
```

---

### `boomerang_score.services.persistence`

Load/save competition state.

#### `CompetitionRepository`

```python
class CompetitionRepository:
    def save(competition: Competition, filepath: str) -> None
    def load(filepath: str) -> Competition
    def exists(filepath: str) -> bool
```

**Example:**

```python
from boomerang_score.services.persistence import CompetitionRepository

repo = CompetitionRepository()
repo.save(competition, "my_tournament.json")

loaded = repo.load("my_tournament.json")
```

---

## Usage Example: Custom Script

Want to compute rankings without the GUI? Here's how:

```python
from boomerang_score.core.models import Competition, Participant, DisciplineResult
from boomerang_score.core.scorer import compute_competition_ranks
from boomerang_score.core.constants import DISC_CODE_ACC, DISC_CODE_AUS

# Create competition
comp = Competition(name="My Tournament")

# Add participants
p1 = Participant(name="Alice", number=1)
p1.set_score(DISC_CODE_ACC, DisciplineResult(points=95.0, raw_value=50.0))
p1.set_score(DISC_CODE_AUS, DisciplineResult(points=90.0, raw_value=120.0))
comp.add_participant(p1)

p2 = Participant(name="Bob", number=2)
p2.set_score(DISC_CODE_ACC, DisciplineResult(points=85.0, raw_value=60.0))
p2.set_score(DISC_CODE_AUS, DisciplineResult(points=100.0, raw_value=130.0))
comp.add_participant(p2)

# Compute rankings
ranks = compute_competition_ranks(comp)
print(f"Alice rank: {ranks[1]}")  # 1 (higher score)
print(f"Bob rank: {ranks[2]}")    # 2
```

---

## App Module

### `boomerang_score.app.rss_boomerang`

Main Tkinter application. Not part of the public API (GUI implementation details change frequently). Use `services/` modules instead.

---

## Further Reading

- [Architecture](architecture.md) — Understand the design
- [Contributing](contributing.md) — How to extend the codebase
- Source code in `src/boomerang_score/`

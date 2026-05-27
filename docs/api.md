---
layout: default
title: API Reference
---

# API Reference

Core module documentation for programmers building on or extending Boomerang Score.

## Core Module

### `boomerang_score.core.models`

Data classes representing tournament state.

#### `Competition`

Tournament container.

```python
@dataclass
class Competition:
    title: str = "My Competition"
    logo_path: str | None = None
    participants: dict[int, Participant]   # startnumber -> Participant
    active_disciplines: set[str]

    def add_participant(participant: Participant) -> None
    def remove_participant(startnumber: int) -> None
    def get_participant(startnumber: int) -> Participant | None
    def set_active_disciplines(discipline_codes: set[str]) -> None
    def is_discipline_active(discipline_code: str) -> bool
    def get_all_participants() -> list[Participant]
    def startnumber_exists(startnumber: int) -> bool
    def next_free_startnumber() -> int
```

#### `Participant`

Person in the tournament.

```python
@dataclass
class Participant:
    name: str
    startnumber: int
    disciplines: dict[str, DisciplineResult]  # discipline_code -> result
    total_points: float | None
    overall_rank: int | None

    def get_result(discipline_code: str) -> float | None
    def set_result(discipline_code: str, result: float | None) -> None
    def get_points(discipline_code: str) -> float | None
    def set_points(discipline_code: str, points: float | None) -> None
    def get_rank(discipline_code: str) -> int | None
    def set_rank(discipline_code: str, rank: int | None) -> None
```

#### `DisciplineResult`

Result for one discipline.

```python
@dataclass
class DisciplineResult:
    result: float | None    # Raw measurement (distance, time, count, etc.)
    points: float | None    # Computed points for ranking
    rank: int | None        # Rank within this discipline
```

---

### `boomerang_score.core.scorer`

Scoring logic. Disciplines are defined as `Discipline` objects with a `points_func`.

#### `Discipline`

```python
class Discipline:
    code: str           # e.g. "acc"
    label: str          # e.g. "ACC"
    default_active: bool
    points_func: Callable[[float], float]  # raw result -> points
```

Pre-defined discipline instances (importable from `boomerang_score.core`):

```python
from boomerang_score.core import ACC, AUS, MTA, END, FC, TC, TIMED, TAPIR
```

Each discipline's `points_func` uses a logarithmic scale so that improvements at the top of the scale are harder to achieve than at the bottom.

#### `compute_competition_ranks(items: list[tuple]) -> dict`

Compute standard competition ranking (1, 1, 3, 4, 4, 6, ...) for a list of `(id, value)` pairs. Higher value = better rank.

**Returns:** `{ id: rank }`

```python
from boomerang_score.core.scorer import compute_competition_ranks

ranks = compute_competition_ranks([(1, 95.0), (2, 85.0), (3, 95.0)])
# {1: 1, 3: 1, 2: 3}
```

---

### `boomerang_score.core.constants`

Discipline codes and metadata.

```python
from boomerang_score.core.constants import (
    DISC_CODE_ACC,      # "acc"
    DISC_CODE_AUS,      # "aus"
    DISC_CODE_MTA,      # "mta"
    DISC_CODE_END,      # "end"
    DISC_CODE_FC,       # "fc"
    DISC_CODE_TC,       # "tc"
    DISC_CODE_TIMED,    # "timed"
    DISC_CODE_TAPIR,    # "tapir"
)

DISCIPLINE_LABELS = {
    "acc": "ACC",
    "aus": "AUS",
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
    def __init__(competition: Competition, disciplines: list[Discipline])

    def add_participant(
        name: str,
        startnumber: int,
        discipline_results: dict[str, float] = {}
    ) -> Participant

    def delete_participant(startnumber: int) -> None

    def update_participant_name(startnumber: int, name: str) -> None

    def update_participant_result(
        startnumber: int,
        discipline_code: str,
        result: float
    ) -> None

    def change_startnumber(old_startnumber: int, new_startnumber: int) -> None

    def set_active_disciplines(discipline_codes: set[str]) -> None

    def recalculate_participant(startnumber: int) -> None

    def recalculate_all_ranks() -> None

    def clear_all_data() -> None
```

**Example:**

```python
from boomerang_score.core import Competition, ACC, AUS
from boomerang_score.core.constants import DISC_CODE_ACC, DISC_CODE_AUS
from boomerang_score.services import CompetitionService

comp = Competition(title="Spring Championship")
service = CompetitionService(comp, [ACC, AUS])
service.set_active_disciplines({DISC_CODE_ACC, DISC_CODE_AUS})

# Add participant
p = service.add_participant(
    "John Doe",
    1,
    {DISC_CODE_ACC: 80.5, DISC_CODE_AUS: 95.0}
)

# Update a result
service.update_participant_result(1, DISC_CODE_ACC, 85.0)

# Access computed data
print(comp.participants[1].total_points)
print(comp.participants[1].overall_rank)
```

---

### `boomerang_score.services.export_service`

Document generation.

#### `ExportService`

```python
class ExportService:
    def __init__(competition: Competition, disciplines: list[Discipline])

    def export_csv(filepath: str) -> str
    def export_pdf_full_list(filepath: str) -> str
    def export_individual_reports(output_dir: str) -> list[str]
```

```python
from boomerang_score.core import Competition, ACC, AUS
from boomerang_score.services import ExportService

export_service = ExportService(competition, [ACC, AUS])
export_service.export_csv("results.csv")
export_service.export_pdf_full_list("results.pdf")
```

---

### `boomerang_score.services.persistence`

Load/save competition state.

#### `CompetitionRepository`

```python
class CompetitionRepository:
    def save(competition: Competition, filepath: str) -> None
    def load(filepath: str) -> Competition
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
from boomerang_score.core import Competition, ACC, AUS, MTA
from boomerang_score.core.constants import DISC_CODE_ACC, DISC_CODE_AUS, DISC_CODE_MTA
from boomerang_score.services import CompetitionService

# Create competition
comp = Competition(title="My Tournament")
service = CompetitionService(comp, [ACC, AUS, MTA])
service.set_active_disciplines({DISC_CODE_ACC, DISC_CODE_AUS, DISC_CODE_MTA})

# Add participants
service.add_participant("Alice", 1, {DISC_CODE_ACC: 80.0, DISC_CODE_AUS: 95.0})
service.add_participant("Bob", 2, {DISC_CODE_ACC: 60.0, DISC_CODE_AUS: 110.0})

# Rankings are computed automatically
for startnr, p in comp.participants.items():
    print(f"#{startnr} {p.name}: {p.total_points:.1f} pts, rank {p.overall_rank}")
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

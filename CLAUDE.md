# Boomerang Score

A Python application for scoring boomerang tournaments. Supports 8 discipline events: accuracy (ACC), Australian round (AUS), maximum time aloft (MTA), endurance (END), fast catch (FC), trick catch (TC), timed catch (TIMED), and tapir (TAPIR). The app provides a Tkinter GUI for data entry, participant ranking, and document export (Word and PDF).

## Quick Start

### Run the App

```bash
uv run boomerang-score
```

Or directly:

```bash
uv run python -m boomerang_score
```

### Run Tests

```bash
uv run pytest test/
```

With coverage (business logic only):

```bash
uv run pytest test/ \
  --cov=src/boomerang_score/core \
  --cov=src/boomerang_score/services \
  --cov-report=term-missing \
  --cov-fail-under=80
```

### Lint and Format

Check:

```bash
uv run ruff check src/ test/
uv run ruff format --check src/ test/
```

Fix:

```bash
uv run ruff check --fix src/ test/
uv run ruff format src/ test/
```

Pre-commit hooks run these automatically on `git commit`.

## Architecture

The codebase follows a three-layer architecture with strict separation of concerns:

### 1. Core Domain (`src/boomerang_score/core/`)

Purely functional, framework-agnostic business logic.

- **`models.py`** — Data classes: `Competition`, `Participant`, `DisciplineResult`. No side effects.
- **`scorer.py`** — Scoring computations: `compute_competition_ranks()` and discipline-specific scoring functions.
- **`constants.py`** — Discipline codes, labels, and constants for all 8 events.

**Rule:** No imports from `app/` or `services/`. No external I/O.

### 2. Services (`src/boomerang_score/services/`)

Business logic that orchestrates the core and manages I/O (file persistence, document export).

- **`competition_service.py`** — Tournament operations (add participant, compute rankings, etc.). Uses `core/` models and `scorer.py`.
- **`export_service.py`** — Export to Word (`.docx`) and PDF documents. Uses `reportlab` and `python-docx`.
- **`persistence.py`** — Load/save competition state to disk (JSON).

**Rule:** Imports `core/` freely. No imports from `app/`. All external I/O happens here.

### 3. App (GUI) (`src/boomerang_score/app/`)

Tkinter interface. Handles user interaction, event binding, and display.

- **`rss_boomerang.py`** — Main `ScoreTableApp` class. Coordinates the GUI layout, event handlers, and calls into `services/`.
- **`components/`** — Reusable UI components (menu bar, discipline panel, table view, etc.).

**Rule:** Pure UI logic only. All business logic calls go through `services/`. No scoring, no data transformations.

**Why this split matters:**
- Core and services are fully testable without Tkinter.
- GUI is thin: it displays state and dispatches actions, but doesn't compute or transform data.
- New CLIs, APIs, or headless tools can reuse core + services without the GUI.
- Tests focus on coverage of core + services (target 80%+).

## Testing Strategy

### Business Logic Tests (Core + Services)

All tests live in `test/`:

```
test/
├── core/
│   ├── test_models.py       — Participant, Competition, DisciplineResult
│   └── test_scoring.py      — Scoring functions, ranking computation
└── services/
    ├── test_competition_service.py   — Tournament operations
    ├── test_export_service.py        — Export to Word/PDF
    └── test_persistence.py           — Load/save
```

These tests must achieve **80%+ coverage**. Use `/test` skill to check.

### GUI Testing

GUI logic is inherently hard to test automatically (Tkinter widgets, event loops, display state). Instead:

- **Minimal business logic in `app/`** — keep the GUI thin.
- **Audit regularly** — use `/gui-audit` skill to identify logic that has leaked into the GUI and should be extracted to `services/`.
- **Manual testing** — run the app, interact with it, verify behavior. This is how bugs in the GUI layer are caught.

## Development Workflow

### Pre-Commit Hooks

Configured in `.pre-commit-config.yaml`. Runs on every `git commit`:

- `ruff check --fix` — linting with auto-fix
- `ruff-format` — code formatting

Install hooks (one-time):

```bash
uv run pre-commit install
```

Run manually on all files:

```bash
uv run pre-commit run --all-files
```

### Making Changes

1. Create a branch: `git checkout -b feature/your-feature`
2. Edit code, add tests.
3. Run tests and linting: `/test` and `/lint` skills.
4. Commit: `git commit` (hooks run automatically).
5. Push and open a PR.

### Skills (Claude Code)

Available in `.claude/commands/`:

- **`/test`** — Run pytest with coverage, identify gaps in business logic.
- **`/lint`** — Run ruff check and format.
- **`/setup-precommit`** — Install and configure pre-commit hooks.
- **`/update-docs`** — Keep CLAUDE.md in sync with the codebase.
- **`/gui-audit`** — Identify untestable GUI logic and propose extractions.

## Dependencies

### Runtime

- `python-docx >= 1.2.0` — Export to Word (`.docx`)
- `reportlab >= 4.4.10` — Export to PDF

### Dev

- `pytest >= 9.0.2` — Testing framework
- `pytest-cov >= 7.1.0` — Coverage reporting
- `pyinstaller >= 6.0.0` — Build standalone executables
- `pre-commit >= 4.6.0` — Git hooks
- `ruff >= 0.15.12` — Linting and formatting

### Python Version

Requires **Python 3.10–3.13** (see `pyproject.toml`). Pinned to 3.10 because Tkinter requires the system Python on some platforms (Linux, macOS) for proper font rendering and X11 support.

## CI/CD

GitHub Actions (`.github/workflows/ci.yml`):

1. **Test job** — Runs `uv sync --dev && pytest` across macOS, Ubuntu, Windows with Python 3.10–3.13.
2. **Build job** — Builds wheel package if tests pass.

Both main and PR branches trigger the workflow (see `.github/workflows/`).

## Project Layout

```
boomerang-score/
├── src/boomerang_score/
│   ├── __main__.py              — Entry point
│   ├── core/                    — Domain logic (no side effects)
│   │   ├── models.py
│   │   ├── scorer.py
│   │   ├── constants.py
│   │   └── __init__.py
│   ├── services/                — Business logic + I/O
│   │   ├── competition_service.py
│   │   ├── export_service.py
│   │   ├── persistence.py
│   │   └── __init__.py
│   └── app/                     — GUI (thin layer)
│       ├── rss_boomerang.py
│       ├── components/
│       └── __init__.py
├── test/
│   ├── core/
│   ├── services/
│   └── conftest.py              — Shared pytest fixtures
├── pyproject.toml               — Project config, dependencies, scripts
├── .pre-commit-config.yaml      — Git hook config (ruff check + format)
├── .github/workflows/
│   ├── ci.yml                   — Test and build automation
│   ├── build-executables.yml    — PyInstaller builds
│   └── release.yml              — Release automation
└── CLAUDE.md                    — This file
```

## Key Patterns

### Scoring Flow

```
GUI (app/) 
  → calls CompetitionService.add_participant() 
    → uses Scorer.compute_competition_ranks() (core)
    → updates Competition model
  → displays updated rankings
```

### Export Flow

```
GUI (app/) 
  → calls ExportService.export_to_pdf() 
    → reads Competition model 
    → formats with reportlab 
    → writes file 
  → displays success
```

### Persistence Flow

```
GUI (app/) 
  → calls CompetitionRepository.save() 
    → writes JSON to disk 
  → or loads with CompetitionRepository.load()
```

## Testing Discipline Scoring

Each discipline has its own scoring function in `core/scorer.py`. Test them independently:

```python
from boomerang_score.core.scorer import score_accuracy

result = score_accuracy(distances=[80.0, 75.0, 70.0], catches=3)
assert result.points == 100
```

No GUI, no I/O, no fixtures needed. Add tests to `test/core/test_scoring.py`.

## Further Reading

- **Scoring rules** — See `constants.py` and `scorer.py` for discipline rules and point calculations.
- **Export formats** — See `export_service.py` for how Word and PDF documents are structured.
- **GUI events** — See `app/rss_boomerang.py` for event binding patterns and how actions dispatch to `services/`.

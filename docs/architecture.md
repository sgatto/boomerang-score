---
layout: default
title: Architecture
---

# Architecture

Boomerang Score follows a **three-layer architecture** with strict separation of concerns:

```
┌─────────────────────────────────────┐
│  GUI (Tkinter)                      │
│  app/                               │
├─────────────────────────────────────┤
│  Business Logic & I/O               │
│  services/                          │
├─────────────────────────────────────┤
│  Domain Model (no side effects)     │
│  core/                              │
└─────────────────────────────────────┘
```

## Layer 1: Core (Domain Logic)

**Location:** `src/boomerang_score/core/`

Pure, framework-agnostic business logic. No external I/O, no side effects.

### Modules

- **`models.py`** — Data classes
  - `Competition` — Tournament with participants and results
  - `Participant` — Person with scores across disciplines
  - `DisciplineResult` — Raw and computed scores for one event

- **`scorer.py`** — Scoring functions
  - `compute_competition_ranks()` — Rank all participants across all disciplines
  - Per-discipline scoring: `score_accuracy()`, `score_timed_catch()`, etc.

- **`constants.py`** — Discipline codes and metadata
  - 8 discipline constants: `DISC_CODE_ACC`, `DISC_CODE_AUS`, etc.
  - Points-per-placement rules for each discipline

### Why It's Separate

- Fully testable without GUI
- Reusable by other interfaces (CLI, API, batch scripts)
- Easy to modify scoring rules without touching the GUI
- No external dependencies (pure Python)

## Layer 2: Services (Business Logic + I/O)

**Location:** `src/boomerang_score/services/`

Orchestrates the core layer and handles file I/O, document generation, persistence.

### Modules

- **`competition_service.py`** — Tournament operations
  - `add_participant(name, number, scores)` — Add a person to competition
  - `remove_participant(number)` — Remove a participant
  - `update_score(number, discipline_code, score)` — Update a single score
  - Calls `core.scorer` to recompute rankings

- **`export_service.py`** — Document export
  - `export_to_pdf(competition, filename)` — Generate PDF report
  - `export_to_word(competition, filename)` — Generate Word document
  - Uses `reportlab` and `python-docx`

- **`persistence.py`** — Load/save competition state
  - `CompetitionRepository.save(competition, filepath)` — Write to JSON
  - `CompetitionRepository.load(filepath)` — Read from JSON
  - No external APIs; purely file-based

### Why It's Separate

- Bundles related operations (e.g., all tournament logic together)
- Encapsulates I/O; the GUI doesn't need to know how data is stored
- Easy to test with mocks (mock file I/O, mock document generation)
- Can be reused by other frontends

## Layer 3: App (GUI)

**Location:** `src/boomerang_score/app/`

Tkinter interface. Displays state, captures user input, dispatches actions.

### Structure

- **`rss_boomerang.py`** — Main `ScoreTableApp` class
  - Builds the Tkinter window layout (menu bar, frames, table)
  - Binds event handlers (button clicks, table edits, menu selections)
  - Calls `services.*` methods in response to user actions
  - Updates display with results

- **`components/`** — Reusable UI widgets
  - `MenuBar` — "File", "Edit" menus
  - `DisciplinePanel` — Discipline selector with checkboxes
  - `TableView` — Ttk.Treeview for participant scores

### What Stays Here

- Widget creation and layout
- Event binding
- Display formatting (colors, fonts, column widths)
- Window management

### What Doesn't Belong Here

- Scoring logic → `core.scorer`
- Data persistence → `services.persistence`
- Document export → `services.export`
- Tournament operations → `services.competition_service`

If you find yourself computing, validating, or transforming data in the GUI layer, extract it to `services/`.

## Data Flow

### Add a Participant

```
GUI
  User clicks "Add Participant" button
  
→ CompetitionService.add_participant(name, number, scores)
  Creates Participant model
  Calls Scorer.compute_competition_ranks()
  Returns updated Competition
  
→ GUI
  Re-displays table with new participant and updated ranks
```

### Export to PDF

```
GUI
  User clicks "Export" > "PDF"
  
→ ExportService.export_to_pdf(competition, filename)
  Reads Competition model
  Formats with reportlab
  Writes file
  Returns success/error
  
→ GUI
  Shows "Export complete" message
```

### Load a Tournament

```
GUI
  User selects "File" > "Open"
  Chooses a JSON file
  
→ CompetitionRepository.load(filepath)
  Reads JSON
  Reconstructs Participant and DisciplineResult objects
  Returns Competition
  
→ GUI
  Displays loaded tournament
```

## Testing Each Layer

### Core Tests

No fixtures, no I/O, no GUI. Test scoring logic directly:

```python
from boomerang_score.core.scorer import score_accuracy

result = score_accuracy(distances=[80.0, 75.0], catches=2)
assert result.points == 100
```

Location: `test/core/test_scoring.py`, `test/core/test_models.py`

### Services Tests

Mock file I/O, test business logic:

```python
def test_add_participant(service, competition):
    service.add_participant("John Doe", 1, {DISC_CODE_ACC: 50.0})
    
    assert len(competition.participants) == 1
    assert competition.get_participant(1).name == "John Doe"
```

Location: `test/services/test_competition_service.py`, etc.

### GUI Tests

Manual or integration. GUI logic is tested by running the app and interacting with it. Use `/gui-audit` to identify logic that should be moved to `services/` and tested there.

## Adding a New Feature

### Example: Add a "Export to CSV" function

1. **Add to services** (`services/export_service.py`):
   ```python
   def export_to_csv(competition, filename):
       # Write CSV logic here
       # No Tkinter imports
   ```

2. **Add test** (`test/services/test_export_service.py`):
   ```python
   def test_export_csv(competition):
       path = export_to_csv(competition, "test.csv")
       assert Path(path).exists()
   ```

3. **Wire up GUI** (`app/rss_boomerang.py`):
   ```python
   def on_export_csv(self):
       filename = filedialog.asksaveasfilename(filetypes=[("CSV", "*.csv")])
       if filename:
           export_to_csv(self.competition, filename)
           messagebox.showinfo("Success", "Exported to CSV")
   ```

This keeps the logic testable (services) and the GUI thin (app).

## Dependency Inversion

The app depends on services, which depend on core. Core has no dependencies on other layers. This makes it easy to test each layer independently and swap implementations (e.g., replace Tkinter with PyQt without changing core or services).

```
app/ → services/ → core/
     (no back edges)
```

## Further Reading

- [Scoring Rules](scoring-rules.md) — How points are calculated per discipline
- [Contributing](contributing.md) — How to modify and test the codebase
- Main CLAUDE.md for development setup

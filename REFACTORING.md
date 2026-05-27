# Refactoring Summary

The application has been refactored to separate domain logic from GUI code.

## New Structure

```
src/boomerang_score/
├── core/
│   ├── __init__.py
│   ├── models.py              # Domain models (Participant, Competition, DisciplineResult)
│   ├── constants.py           # Discipline code and label constants
│   └── scorer.py              # Scoring and ranking logic
├── services/
│   ├── __init__.py
│   ├── competition_service.py # Business logic for managing competitions
│   ├── export_service.py      # Export functionality (CSV, PDF, DOCX)
│   └── persistence.py         # Save/load competitions to/from JSON
├── app/
│   ├── __init__.py
│   ├── rss_boomerang.py       # Main GUI application (~709 lines)
│   └── components/            # GUI components
│       ├── __init__.py
│       ├── table_view.py      # TreeView with sorting and inline editing
│       ├── input_panel.py     # Participant input form
│       ├── discipline_panel.py # Discipline selection checkboxes
│       └── menu_bar.py        # Menu and export actions
├── cli.py                     # Command-line interface
└── test/
    ├── core/
    │   ├── test_models.py     # Tests for domain models
    │   └── test_scoring.py    # Scoring logic tests
    └── services/
        ├── test_competition_service.py  # Tests for business logic
        ├── test_export_service.py       # Tests for export functionality
        └── test_persistence.py          # Tests for save/load
```

## What Changed

### 1. Domain Models (`core/models.py`)

**Classes:**
- `DisciplineResult`: Stores result, points, and rank for a single discipline
- `Participant`: Represents a competitor with name, startnumber, and discipline results
- `Competition`: Contains participants, active disciplines, title, and logo

**Benefits:**
- Type-safe data structures
- Clear data model independent of GUI
- Validation logic in one place
- Easy to test

### 2. Business Logic (`services/competition_service.py`)

**CompetitionService** handles:
- Adding/updating participants
- Calculating points and ranks
- Managing active disciplines
- Validation (duplicate startnumbers, etc.)

**Benefits:**
- Can be tested without GUI
- Reusable in CLI, web, or other interfaces
- Business rules in one place

### 3. Export Logic (`services/export_service.py`)

**ExportService** provides:
- `export_csv()`: Export to CSV format
- `export_pdf_full_list()`: Full competition list PDF
- `export_individual_reports()`: Individual awards (PDF/DOCX)

**Benefits:**
- Separated from GUI file dialogs
- Can be called from command line
- Easy to test with sample data
- No GUI dependencies

### 4. Persistence (`services/persistence.py`)

**CompetitionRepository** provides:
- `save(competition, path)`: Serialize Competition to JSON
- `load(path)`: Deserialize Competition from JSON

**Benefits:**
- Users can save work and continue later
- Share competition files between users
- Backup and version control

### 5. Constants (`core/constants.py`)

Discipline codes and labels defined as named constants (e.g. `DISC_CODE_FC = "fc"`),
used throughout the codebase to avoid magic strings.

## Completed Refactoring (Phase 1)

✅ **Domain Models** - Clean data structures with validation
✅ **Service Layer** - Business logic separated from GUI
✅ **Component Architecture** - GUI split into reusable components:
   - Main app reduced from 877 lines; grew back to ~709 with new features (persistence, file menu, exports)
   - TableView, InputPanel, DisciplinePanel, MenuBar components
✅ **Unit Tests** - 101 tests covering models, scoring, services, export, and persistence (all passing)
✅ **Type Hints** - Added to core models, services, and components
✅ **CLI Interface** - Command-line tool for programmatic access
✅ **Startnumber as ID** - Immutable startnumber replaces arbitrary IDs:
   - `Competition.participants` is now `dict[int, Participant]`
   - `service.add_participant(name, startnumber, results) -> Participant`
   - All methods use `startnumber: int` instead of `participant_id: str`
   - Removed `update_startnumber()` method (startnumber is immutable)
   - Cleaner, more intuitive API
✅ **Persistence** - Save/Load competition to/from JSON (`CompetitionRepository`)
✅ **File Menu** - New / Open / Save / Save As in GUI
✅ **Remove Legacy Adapter** - `adapter.py` removed; GUI uses `competition.participants` directly
✅ **Export Tests** - `test/services/test_export_service.py` added
✅ **Persistence Tests** - `test/services/test_persistence.py` added
✅ **Constants** - Discipline codes extracted to `core/constants.py`

## Next Steps (Phase 2)

### 1. **Recent Files**
**Priority: HIGH**

- [ ] Track recently opened competition files
- [ ] Display in File menu for quick access

---

### 2. **Enhanced CLI with Persistence**
**Priority: MEDIUM**

Make CLI more useful by adding file operations:

- [ ] **Load competition**: `boomerang-score load competition.json`
- [ ] **Interactive mode**: REPL for managing competitions
- [ ] **Batch operations**: Import participants from CSV
- [ ] **Competition info**: Show statistics, summaries

**Example workflow:**
```bash
# Create new competition
boomerang-score new --title "Spring Championship 2025" --output comp.json

# Add participants
boomerang-score add comp.json "John Doe" --acc 85 --aus 120
boomerang-score add comp.json "Jane Smith" --acc 90 --aus 115

# View results
boomerang-score list comp.json --sort rank

# Export
boomerang-score export comp.json pdf results.pdf
```

---

### 3. **GUI Improvements**
**Priority: MEDIUM**

- [ ] **Undo/Redo**: Track changes and allow reverting
- [ ] **Search/Filter**: Find participants by name or number
- [ ] **Bulk Edit**: Update multiple participants at once
- [ ] **Validation Feedback**: Real-time input validation with visual cues
- [ ] **Keyboard Shortcuts**: Improve workflow efficiency
- [ ] **Dark Mode**: Theme support

---

### 4. **Testing Enhancements**
**Priority: MEDIUM**

- [ ] **GUI Tests**: Add tests for components using pytest-qt or similar
- [ ] **Integration Tests**: Test full workflows (add participant → calculate → export)
- [ ] **Coverage**: Aim for >80% code coverage (GUI code currently untested)

**Files to create:**
- `test/app/test_components.py`
- `test/integration/test_workflows.py`

---

### 5. **Documentation**
**Priority: LOW**

- [ ] **User Guide**: How to use the application
- [ ] **Developer Guide**: Architecture and contribution guidelines
- [ ] **API Documentation**: Sphinx/ReadTheDocs for services
- [ ] **Tutorial**: Step-by-step walkthrough
- [ ] **Video Demo**: Screen recording of features

---

### 6. **Distribution & Packaging**
**Priority: LOW**

- [ ] **Executable**: PyInstaller/cx_Freeze for standalone app
- [ ] **Installers**: Windows MSI, macOS DMG, Linux AppImage
- [ ] **PyPI Package**: Publish for `pip install boomerang-score`
- [ ] **Desktop Entry**: Linux .desktop file, Windows shortcuts

---

### 7. **Advanced Features**
**Priority: LOW**

- [ ] **Multi-Language Support**: i18n/l10n for different languages
- [ ] **Custom Disciplines**: Allow users to define their own scoring rules
- [ ] **Competition Templates**: Pre-configured setups for common formats
- [ ] **Live Scoring**: Update results during competition
- [ ] **Web Dashboard**: Flask/FastAPI web interface for remote access
- [ ] **Cloud Sync**: Optional cloud backup and sharing

---

## Recommended Implementation Order

1. **Recent Files** (quick win) - Most requested UX improvement
2. **Enhanced CLI** - Make CLI production-ready with file operations
3. **GUI Improvements** - Polish user experience
4. **Testing** - Ensure quality and prevent regressions
5. **Documentation** - Help users and contributors
6. **Distribution** - Make app easy to install
7. **Advanced Features** (Future) - Based on user feedback

## Usage Example

```python
from boomerang_score.core import Competition, ACC, AUS, MTA
from boomerang_score.services import CompetitionService

# Create competition
comp = Competition(title="My Tournament")
comp.set_active_disciplines({"acc", "aus", "mta"})

# Create service
service = CompetitionService(comp, [ACC, AUS, MTA])

# Add participant (startnumber is the unique ID)
service.add_participant(
    name="John Doe",
    startnumber=1,
    discipline_results={"acc": 45.2, "aus": 88.5, "mta": 25.0}
)

# Results are automatically calculated
participant = comp.participants[1]
print(f"Total: {participant.total_points}")
print(f"ACC Points: {participant.get_points('acc')}")
print(f"Overall Rank: {participant.overall_rank}")
```

## Testing

Run tests with:
```bash
PYTHONPATH=src python -m pytest test/ -v
```

## Refactoring Metrics

### Code Organization
- **Main app**: 877 lines → ~709 lines (note: grew back from post-refactor 380 due to persistence, file menu, and export features)
- **New components**: ~655 lines across 4 focused modules
- **Test coverage**: 101 tests (models + scoring + competition service + export service + persistence)
- **All tests**: ✅ PASSING

### Architecture Improvements
- **Separation of Concerns**: Domain/Service/GUI layers clearly defined
- **Testability**: Core logic testable without GUI
- **Reusability**: Services usable from CLI, web, or other interfaces
- **Maintainability**: Smaller, focused files easier to understand
- **Type Safety**: Type hints throughout core and services

### New Capabilities
- ✅ Command-line interface for automation
- ✅ Programmatic API for scripting
- ✅ Component-based GUI architecture
- ✅ Comprehensive test suite
- ✅ Save/Load competition files (JSON)
- ✅ File menu (New / Open / Save / Save As)

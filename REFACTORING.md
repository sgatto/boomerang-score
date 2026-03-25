# Refactoring Summary

The application has been refactored to separate domain logic from GUI code.

## New Structure

```
src/boomerang_score/
├── core/
│   ├── __init__.py
│   ├── models.py              # Domain models (Participant, Competition, DisciplineResult)
│   └── scorer.py              # Scoring and ranking logic
├── services/
│   ├── __init__.py
│   ├── competition_service.py # Business logic for managing competitions
│   └── export_service.py      # Export functionality (CSV, PDF, DOCX)
├── app/
│   ├── __init__.py
│   ├── rss_boomerang.py       # Main GUI application (refactored - 380 lines)
│   ├── adapter.py             # Legacy data adapter for backward compatibility
│   └── components/            # GUI components
│       ├── __init__.py
│       ├── table_view.py      # TreeView with sorting and inline editing
│       ├── input_panel.py     # Participant input form
│       ├── discipline_panel.py # Discipline selection checkboxes
│       └── menu_bar.py        # Menu and export actions
├── cli.py                     # Command-line interface
└── test/
    ├── core/
    │   ├── test_models.py     # 30 tests for domain models
    │   └── test_scoring.py    # Scoring logic tests
    └── services/
        └── test_competition_service.py  # 19 tests for business logic
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

## Completed Refactoring (Phase 1)

✅ **Domain Models** - Clean data structures with validation
✅ **Service Layer** - Business logic separated from GUI
✅ **Component Architecture** - GUI split into reusable components:
   - Main app reduced from 877 to 380 lines (57% reduction)
   - TableView, InputPanel, DisciplinePanel, MenuBar components
✅ **Unit Tests** - 47 tests covering models and services (all passing)
✅ **Type Hints** - Added to core models, services, and components
✅ **CLI Interface** - Command-line tool for programmatic access
✅ **Startnumber as ID** - Immutable startnumber replaces arbitrary IDs:
   - `Competition.participants` is now `dict[int, Participant]`
   - `service.add_participant(name, startnumber, results) -> Participant`
   - All methods use `startnumber: int` instead of `participant_id: str`
   - Removed `update_startnumber()` method (startnumber is immutable)
   - Cleaner, more intuitive API

## Next Steps (Phase 2)

### 1. **Persistence & Data Management**
**Priority: HIGH**

Currently, data only exists in memory during app runtime. Add persistence:

- [ ] **Save/Load Competition**: Serialize Competition to JSON/pickle
  - Add `CompetitionRepository` service
  - Implement `save_to_file()` and `load_from_file()` methods
  - Add "File" menu with New/Open/Save/Save As
  - Auto-save on changes (optional)

- [ ] **Recent Files**: Track and display recently opened competitions

**Benefits:**
- Users can save their work and continue later
- Share competition files between users
- Backup and version control

**Files to create:**
- `src/boomerang_score/services/persistence.py`
- `test/services/test_persistence.py`

---

### 2. **Remove Legacy Adapter**
**Priority: MEDIUM**

The `LegacyDataAdapter` was created for backward compatibility but adds complexity:

- [ ] **Refactor components** to work directly with Competition/Participant models
- [ ] **Remove adapter.py** once all components updated
- [ ] **Simplify TableView** to use Competition.participants directly

**Benefits:**
- Cleaner codebase
- Better performance (no adapter overhead)
- More maintainable

---

### 3. **Enhanced CLI with Persistence**
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

### 4. **GUI Improvements**
**Priority: MEDIUM**

- [ ] **Undo/Redo**: Track changes and allow reverting
- [ ] **Search/Filter**: Find participants by name or number
- [ ] **Bulk Edit**: Update multiple participants at once
- [ ] **Validation Feedback**: Real-time input validation with visual cues
- [ ] **Keyboard Shortcuts**: Improve workflow efficiency
- [ ] **Dark Mode**: Theme support

---

### 5. **Testing Enhancements**
**Priority: MEDIUM**

- [ ] **GUI Tests**: Add tests for components using pytest-qt or similar
- [ ] **Integration Tests**: Test full workflows (add participant → calculate → export)
- [ ] **Export Tests**: Verify CSV/PDF/DOCX output correctness
- [ ] **Coverage**: Aim for >80% code coverage

**Files to create:**
- `test/app/test_components.py`
- `test/integration/test_workflows.py`
- `test/services/test_export_service.py`

---

### 6. **Documentation**
**Priority: LOW**

- [ ] **User Guide**: How to use the application
- [ ] **Developer Guide**: Architecture and contribution guidelines
- [ ] **API Documentation**: Sphinx/ReadTheDocs for services
- [ ] **Tutorial**: Step-by-step walkthrough
- [ ] **Video Demo**: Screen recording of features

---

### 7. **Distribution & Packaging**
**Priority: LOW**

- [ ] **Executable**: PyInstaller/cx_Freeze for standalone app
- [ ] **Installers**: Windows MSI, macOS DMG, Linux AppImage
- [ ] **PyPI Package**: Publish for `pip install boomerang-score`
- [ ] **Desktop Entry**: Linux .desktop file, Windows shortcuts

---

### 8. **Advanced Features**
**Priority: LOW**

- [ ] **Multi-Language Support**: i18n/l10n for different languages
- [ ] **Custom Disciplines**: Allow users to define their own scoring rules
- [ ] **Competition Templates**: Pre-configured setups for common formats
- [ ] **Live Scoring**: Update results during competition
- [ ] **Web Dashboard**: Flask/FastAPI web interface for remote access
- [ ] **Cloud Sync**: Optional cloud backup and sharing

---

## Recommended Implementation Order

1. **Persistence** (Week 1) - Most critical for users to save work
2. **Remove Adapter** (Week 1) - Simplify codebase while fresh in mind
3. **Enhanced CLI** (Week 2) - Make CLI production-ready
4. **GUI Improvements** (Week 2-3) - Polish user experience
5. **Testing** (Week 3) - Ensure quality and prevent regressions
6. **Documentation** (Week 4) - Help users and contributors
7. **Distribution** (Week 4) - Make app easy to install
8. **Advanced Features** (Future) - Based on user feedback

## Usage Example

```python
from boomerang_score.core import Competition, Participant, ACC, AUS, MTA
from boomerang_score.services import CompetitionService

# Create competition
comp = Competition(title="My Tournament")
comp.set_active_disciplines({"acc", "aus", "mta"})

# Create service
service = CompetitionService(comp, [ACC, AUS, MTA])

# Add participant
service.add_participant(
    participant_id="p1",
    name="John Doe",
    startnumber=1,
    discipline_results={"acc": 45.2, "aus": 88.5, "mta": 25.0}
)

# Results are automatically calculated
participant = comp.get_participant("p1")
print(f"Total: {participant.total_points}")
print(f"ACC Points: {participant.get_points('acc')}")
print(f"Overall Rank: {participant.overall_rank}")
```

## Testing

The refactored code is now testable:

```python
# test/core/test_models.py
def test_participant_validation():
    with pytest.raises(ValueError):
        Participant(name="", startnumber=1)  # Empty name

# test/services/test_competition_service.py
def test_add_participant():
    comp = Competition()
    service = CompetitionService(comp, [ACC])
    service.add_participant("p1", "John", 1, {"acc": 50.0})
    assert len(comp.participants) == 1
```

Run tests with:
```bash
PYTHONPATH=src python -m pytest test/ -v
```

## Refactoring Metrics

### Code Organization
- **Main app**: 877 lines → 380 lines (57% reduction)
- **New components**: 655 lines across 4 focused modules
- **Test coverage**: 50 tests (30 models + 19 services + 1 scoring)
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

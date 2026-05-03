---
layout: default
title: Contributing
---

# Contributing

Thank you for interest in improving Boomerang Score! This guide explains the development workflow, testing expectations, and code standards.

## Development Workflow

### 1. Clone and Set Up

```bash
git clone https://github.com/sgatto/boomerang-score.git
cd boomerang-score

# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming:
- `feature/` for new features
- `fix/` for bug fixes
- `docs/` for documentation
- `refactor/` for refactoring

### 3. Make Changes

- Write code
- Add tests (see [Testing](#testing) below)
- Run linting and formatting
- Commit with clear messages

### 4. Test and Lint

```bash
# Run all tests
uv run pytest test/

# Run with coverage (must be 80%+ for core/ and services/)
uv run pytest test/ \
  --cov=src/boomerang_score/core \
  --cov=src/boomerang_score/services \
  --cov-fail-under=80

# Lint and format
uv run ruff check src/ test/
uv run ruff format src/ test/
```

The `/test` and `/lint` skills (Claude Code) automate these steps.

### 5. Commit

```bash
git commit -m "Describe what changed and why"
```

Pre-commit hooks run automatically:
- `ruff check --fix` (linting)
- `ruff-format` (formatting)

If hooks fail, fix the issues and commit again.

### 6. Push and Open a PR

```bash
git push origin feature/your-feature-name
```

Then open a pull request on GitHub. Fill in the PR template and link any related issues.

## Testing

### Test Structure

```
test/
├── core/
│   ├── test_models.py       — Test Participant, Competition, DisciplineResult
│   └── test_scoring.py      — Test scoring functions per discipline
└── services/
    ├── test_competition_service.py   — Test tournament operations
    ├── test_export_service.py        — Test Word/PDF export
    └── test_persistence.py           — Test load/save
```

### Writing Tests

Tests use pytest. Example:

```python
import pytest
from boomerang_score.core.models import Participant

def test_participant_creation():
    p = Participant(name="John Doe", number=1)
    assert p.name == "John Doe"
    assert p.number == 1
```

**Guidelines:**

- **One concept per test** — Test a single behavior
- **Use descriptive names** — `test_scoring_accuracy_with_multiple_distances()` not `test_1()`
- **Arrange-Act-Assert** — Setup, execute, verify
- **No GUI in tests** — If you find yourself importing `tkinter`, move logic to `services/` first
- **Mock external I/O** — Use `unittest.mock` or `pytest` fixtures to mock file reads/writes, not actual files

Example fixture:

```python
@pytest.fixture
def competition():
    return Competition(name="Test Tournament")

def test_add_participant(competition):
    p = Participant(name="Alice", number=1)
    competition.add_participant(p)
    assert len(competition.participants) == 1
```

### Coverage Requirements

- **Core** (`src/boomerang_score/core/`) — **80%+ coverage required**
- **Services** (`src/boomerang_score/services/`) — **80%+ coverage required**
- **App** (`src/boomerang_score/app/`) — Tested via manual testing and `/gui-audit`

Run coverage check:

```bash
uv run pytest test/ \
  --cov=src/boomerang_score/core \
  --cov=src/boomerang_score/services \
  --cov-report=term-missing \
  --cov-fail-under=80
```

If below 80%, the build fails. Add tests for uncovered lines.

## Code Style

### Conventions

- **Python 3.10+** — Use modern syntax (walrus operator, type hints, etc.)
- **Ruff** — Linting and formatting tool (auto-run via pre-commit)
- **Type hints** — Encouraged for function signatures, especially in `core/`
- **No comments unless needed** — Code should be self-explanatory. Comments explain *why*, not *what*.

### Architecture Rules

See [Architecture](architecture.md) for details. Summary:

- **`core/`** — No imports from `app/` or `services/`. No side effects.
- **`services/`** — Imports `core/` freely. No imports from `app/`. All I/O happens here.
- **`app/`** — Pure UI logic. Calls `services/` for all business logic.

If your change breaks these rules, refactor to restore separation.

## Adding a Feature

### Example: Add "Export to CSV"

1. **Plan in `services/`** (tested, reusable):
   ```python
   # services/export_service.py
   def export_to_csv(competition: Competition, filepath: str) -> str:
       """Export competition to CSV file."""
       # implementation
       return filepath
   ```

2. **Test it** (`test/services/test_export_service.py`):
   ```python
   def test_export_csv(competition, tmp_path):
       path = export_to_csv(competition, str(tmp_path / "out.csv"))
       assert Path(path).read_text().startswith("Participant")
   ```

3. **Wire up the GUI** (`app/rss_boomerang.py`):
   ```python
   def on_export_csv(self):
       filepath = filedialog.asksaveasfilename(filetypes=[("CSV", "*.csv")])
       if filepath:
           export_to_csv(self.competition, filepath)
           messagebox.showinfo("Success", "Exported to CSV")
   ```

4. **Update menu** — Add "Export CSV" to the "File" menu

5. **Test manually** — Run the app and test the feature end-to-end

### Example: Modify Scoring

1. **Change `core/scorer.py`**:
   ```python
   def score_accuracy(distances, catches):
       # New formula here
       return DisciplineResult(...)
   ```

2. **Add test** (`test/core/test_scoring.py`):
   ```python
   def test_score_accuracy_new_formula():
       result = score_accuracy([80.0, 75.0], 2)
       assert result.points == expected_value
   ```

3. **Verify rankings** — Run the app, add a participant, confirm scores update

4. **Commit** — Describe the rule change in the commit message

## Common Tasks

### Run specific test file

```bash
uv run pytest test/core/test_scoring.py -v
```

### Run specific test

```bash
uv run pytest test/core/test_scoring.py::test_score_accuracy_basic -v
```

### Watch tests during development

```bash
uv run pytest test/ --watch
```

(Install `pytest-watch`: `uv add --dev pytest-watch`)

### Check what would be formatted

```bash
uv run ruff format --check src/ test/
```

### Apply all fixes automatically

```bash
uv run ruff check --fix src/ test/
uv run ruff format src/ test/
```

### Build documentation locally

```bash
# Not needed for GitHub Pages; it auto-builds from docs/
# But if you want to test Jekyll locally:
cd docs
bundle install
bundle exec jekyll serve
# Then visit http://localhost:4000/boomerang-score
```

## CI/CD

GitHub Actions automatically run on every push and PR:

1. **Test job** — Runs `pytest` across Python 3.10–3.13 on macOS, Ubuntu, Windows
2. **Build job** — Builds wheel package if tests pass

If tests fail in CI, fix the issues and push again.

## Getting Help

- **Architecture questions** — See [Architecture](architecture.md)
- **How to run/test** — See [Getting Started](getting-started.md) or main CLAUDE.md
- **Scoring details** — See [Scoring Rules](scoring-rules.md)
- **Issues/bugs** — Open a GitHub issue with a clear description

## Code Review

PRs are reviewed for:

- **Coverage** — Core + services must stay at 80%+
- **Architecture** — No layer violations (e.g., `app/` calling `core/` directly)
- **Tests** — New features must have tests
- **Linting** — Passes `ruff check` and `ruff format`
- **Clarity** — Code is readable and maintainable

## Releasing

The maintainers handle releases. If you want to help:

1. Update `version` in `pyproject.toml`
2. Update `CHANGELOG.md` with your changes
3. Create a GitHub release with release notes
4. CI automatically builds wheels and uploads to PyPI

See `.github/workflows/release.yml` for the full process.

Thank you for contributing! 🎉

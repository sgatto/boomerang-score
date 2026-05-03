# /update-docs — Keep CLAUDE.md in sync with the codebase

Read the current project structure and update CLAUDE.md so it accurately reflects how the application works.

## Steps

1. Read the current `CLAUDE.md` (if it exists).

2. Explore the live codebase to capture the current state:
   - `src/boomerang_score/` — module layout, public APIs, entry points
   - `test/` — test structure and what is covered
   - `pyproject.toml` — dependencies, scripts, Python version constraints
   - `.pre-commit-config.yaml` — if it exists
   - `.github/workflows/` — CI steps

3. Compare what CLAUDE.md says against what you find. Update only sections that are **stale or missing**. Do not rewrite sections that are still accurate.

4. CLAUDE.md must always contain:
   - **Project overview** — what the app does (boomerang tournament scoring)
   - **Architecture** — the three-layer structure: `core/` (domain), `services/` (business logic), `app/` (GUI)
   - **How to run** — `uv run boomerang-score` or `uv run python -m boomerang_score`
   - **How to test** — `uv run pytest test/` with coverage flags
   - **How to lint** — `uv run ruff check src/ test/` and `uv run ruff format src/ test/`
   - **Separation of concerns** — what belongs in each layer and why
   - **GUI testing strategy** — explain that `app/` is tested via `/gui-audit`, not unit tests
   - **Pre-commit** — how hooks are set up (if configured)
   - **Dependencies** — key runtime and dev deps

5. Show the user a diff of what changed before saving.

## Goal

Any developer (or Claude in a new session) should be able to read CLAUDE.md and immediately understand how to run, test, and extend the project without guessing.

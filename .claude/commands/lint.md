# /lint — Lint and format with ruff

Check and fix code style across the project using ruff.

## Steps

1. Run ruff check (lint) and report any issues:

```bash
uv run ruff check src/ test/
```

2. Run ruff format check (dry-run) to see what would change:

```bash
uv run ruff format --check src/ test/
```

3. If the user confirms (or if there are only auto-fixable issues), apply fixes:

```bash
uv run ruff check --fix src/ test/
uv run ruff format src/ test/
```

4. Report what was fixed and what (if anything) requires manual attention.

## Notes

- Never silently apply `--fix` without showing the user what will change first.
- Unsafe fixes (`--unsafe-fixes`) require explicit user approval.
- Configuration lives in `pyproject.toml` under `[tool.ruff]`.

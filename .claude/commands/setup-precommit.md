# /setup-precommit — Configure pre-commit with ruff

Set up pre-commit hooks so ruff check and ruff format run automatically before every commit.

## Steps

1. Check if pre-commit is already installed:

```bash
uv run pre-commit --version 2>/dev/null || echo "not installed"
```

2. If not installed, add it to dev dependencies:

```bash
uv add --dev pre-commit
```

3. Check if `.pre-commit-config.yaml` already exists. If not, create it:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0  # use latest stable tag
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

   Before writing, fetch the latest ruff-pre-commit release tag from GitHub to use the correct `rev`.

4. Install the hooks:

```bash
uv run pre-commit install
```

5. Run a dry-run against all files to confirm hooks work:

```bash
uv run pre-commit run --all-files
```

6. Report any failures and fix them before declaring success.

## Notes

- If `.pre-commit-config.yaml` already exists, show the user the current content and ask before modifying.
- The `rev` must match an actual release tag — don't guess; check GitHub or use `pre-commit autoupdate`.

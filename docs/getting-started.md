---
layout: default
title: Getting Started
---

# Getting Started

## Installation

### Requirements

- **Python 3.10–3.13**
- **uv** (Python package manager) — [install here](https://docs.astral.sh/uv/)

### Install from GitHub

```bash
git clone https://github.com/sgatto/boomerang-score.git
cd boomerang-score
uv sync
```

This installs all runtime and dev dependencies.

### Install from PyPI (Coming Soon)

Once published:

```bash
pip install boomerang-score
```

## Run the App

```bash
uv run boomerang-score
```

Or:

```bash
uv run python -m boomerang_score
```

The Tkinter GUI launches in a new window.

## First Tournament

1. **Launch the app** — `uv run boomerang-score`
2. **Create a competition** — Select "File" > "New" or start fresh
3. **Add participants** — Right-click in the table to add a participant
4. **Enter scores** — Input results for each discipline
5. **View rankings** — Standings are computed automatically
6. **Export** — "File" > "Export to PDF" or "Export to Word"

## Development Setup

If you plan to modify the code:

```bash
# Install pre-commit hooks (runs linting/formatting on commit)
uv run pre-commit install

# Run tests
uv run pytest test/

# Run tests with coverage
uv run pytest test/ --cov=src/boomerang_score/core --cov=src/boomerang_score/services

# Lint and format code
uv run ruff check src/ test/
uv run ruff format src/ test/
```

## Troubleshooting

### "tkinter not found" on Linux

On Debian/Ubuntu:

```bash
sudo apt-get install python3-tk python3-dev
```

On Fedora/RHEL:

```bash
sudo dnf install python3-tkinter python3-devel
```

On Arch:

```bash
sudo pacman -S tk
```

Then reinstall:

```bash
uv sync
```

### Font rendering issues on macOS

The app uses system Python for Tkinter. Make sure you're using the Python from `/usr/bin/python3` or a version from python.org (not Homebrew). If issues persist, check `pyproject.toml` for the supported Python version range.

### Permission denied on executable

On macOS/Linux:

```bash
chmod +x ~/.cargo/bin/uv
```

## Next Steps

- Read the [Architecture](architecture.md) to understand how the codebase is structured
- Check [Scoring Rules](scoring-rules.md) for details on how points are calculated
- See [Contributing](contributing.md) to learn the development workflow

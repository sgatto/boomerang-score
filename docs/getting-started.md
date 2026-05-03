---
layout: default
title: Getting Started
---

# Getting Started

## Installation and Run

### Using a pre-built binary
#### Requirements

- OS **Windows** or **macOS**
#### Download the binary
Download the latest release `.exe` (WIN) or `.dmg` (MAC) file from [releases](https://github.com/sgatto/boomerang-score/releases)
#### Run the app
Double-click the downloaded file to run the app.

If the app does not run, check that the file is not corrupted and that the file extension is `.exe` (WIN) or `.dmg` (MAC).

**Note:** The app is not signed, so opening it may prompt a warning, asking if you want to run it anyway (on Windows).
If you do not want to be prompted, you can disable the warning by adding the app to the list of trusted applications in your operating system settings.
On Windows, this can be done by right-clicking the app icon and selecting "More Info" > "Run Anyway".

**Note:** On **macOS**, you may need to allow the app to run in the "Security & Privacy" settings.

### From GitHub sources
#### Requirements

- **Python 3.10–3.13**
- **uv** (Python package manager) — [install here](https://docs.astral.sh/uv/)

#### Install by cloning the repository
Clone the repository and install dependencies:
```bash
git clone https://github.com/sgatto/boomerang-score.git
cd boomerang-score
uv sync
```
#### Run the app
```bash
uv run boomerang-score
```


### Install and run from GitHub whl release
#### Requirements
- **Python 3.10–3.13**
#### Install from whl release
First download a `.whl` package file from [releases](https://github.com/sgatto/boomerang-score/releases)
Then install the `.whl` file by running:
```bash
pip install boomerang-score-*.*.*-py3-none-any.whl
```
This installs the `boomerang-score` python package, its dependencies and its command line shortcut to run the app.
#### Run from the command line
You can run the app directly using the `boomerang-score` command:
```bash
boomerang-score
```

If that doesn't work, you can also run:
```bash
python -m boomerang_score
```

### Install from PyPI (Coming Soon)
#### Requirements
- **Python 3.10–3.13**
#### Install from PyPI
Once `boomerang-score` is published on PyPI, you will be able to install it with:
```bash
pip install boomerang-score
```
This installs the `boomerang-score` python package, its dependencies and its command line shortcut to run the app.
#### Run from the command line
Once installed, you can run the app directly using the `boomerang-score` command, or use `python -m boomerang_score` if needed.


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

## Next Steps

- Read the [Architecture](architecture.md) to understand how the codebase is structured
- Check [Scoring Rules](scoring-rules.md) for details on how points are calculated
- See [Contributing](contributing.md) to learn the development workflow

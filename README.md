# Boomerang score
Small project for scoring boomerang tournaments

Boomerang tournaments are multi-discipline events. Each participant 
usually "throws" 6 different disciplines (or events):
- Accuracy (ACC) 
- australian round (AR)
- endurance (END)
- fast catch (FC)
- MTA (MTA)
- Trick-Catch Doubling (TC)

Each discipline has its on ranking based on the score of the event and
depending on its peculiarities
(minimum time for FC, maximum number of catches for END, etc.).

## General tournament scoring
The scoring systems that has been used for years for the general ranking
is based on sum of placing points obtained on each discipline
- 1 for 1st place
- 2 for 2nd place
- 3 for 3rd place
- etc

The total placing point of each thrower depend on the other throwers' scores.

in with throwers take parts to usually have historically used a scoring system based on the sum
of the ranks of each discipline.

## Installation and Usage

### Prerequisites
- Python 3.12 or newer
- `reportlab` library (will be installed automatically)

### Setup
It is recommended to use a virtual environment.

Using `pip`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

Using `uv`:
```bash
uv sync
```

### Running the application
After installation, you can run the application using:
```bash
boomerang-score
```

Using `uv`:
```bash
uv run boomerang-score
```

Alternatively, without installing:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
python3 -m boomerang_score
```
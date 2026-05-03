# /test — Run tests with coverage

Run the full test suite with coverage and surface any gaps in business logic.

## Steps

1. Run pytest with coverage over `src/boomerang_score/core` and `src/boomerang_score/services` (the business logic layers — GUI is excluded intentionally):

```bash
uv run pytest test/ \
  --cov=src/boomerang_score/core \
  --cov=src/boomerang_score/services \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v
```

2. Read the coverage output and identify any **uncovered lines in `core/` or `services/`**. For each gap:
   - State the file and line range
   - Describe what logic is missing coverage
   - Suggest what test case would cover it

3. If coverage is below 80%, flag it clearly and propose the highest-value tests to write first.

4. Do **not** report coverage gaps in `app/` — GUI coverage is tracked separately via `/gui-audit`.

## Goal

Keep coverage high on all business logic. The GUI layer is hard to test automatically, so `core/` and `services/` must compensate by being fully tested.

# /gui-audit — Identify untestable GUI logic and propose extractions

The GUI layer (`app/`) is hard to unit-test. This skill finds business logic that has leaked into it and proposes how to move it to `core/` or `services/` where it can be tested.

## Steps

1. Read all files under `src/boomerang_score/app/` to map what each component does.

2. For every non-trivial method or block in `app/`, classify it as one of:
   - **Pure UI** — layout, widget config, event binding, display formatting. Leave it here.
   - **Logic leak** — computation, validation, data transformation, or state management that has no dependency on Tkinter widgets. This should be extracted.
   - **Boundary** — calls into `services/` or `core/` correctly. Good pattern.

3. For each **logic leak** found:
   - Quote the relevant code snippet
   - Name the file and line range
   - Propose where it should move (`core/` or `services/`) and what function/method it should become
   - Estimate the test that would cover it once extracted

4. Summarize:
   - Total number of logic leaks found
   - Estimated lines of extractable logic
   - Which files have the most contamination

5. Do **not** make any changes — this is an audit only. If the user wants to act on findings, they will ask separately.

## Goal

Minimize the untestable surface area in the GUI layer. Every non-UI line in `app/` is a line that can't be covered by the test suite. The audit makes this visible so it can be addressed incrementally.

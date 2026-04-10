# Bug Fix: Case Sensitivity in Discipline Codes

## Issue
There was a conflict between uppercase and lowercase discipline codes:
- **Discipline objects** use lowercase `code` (e.g., "acc") for internal keys
- **Discipline objects** use uppercase `label` (e.g., "ACC") for display only
- **Bug**: `table_view.py` was calling `.upper()` on the code when updating results

## Example
```python
# Discipline definition in scorer.py:
ACC = Discipline("acc", "ACC", True, lambda e: _points_100(float(e)))
#                 ^^^^   ^^^^
#                 code   label (display only)

# Column keys in GUI:
key_e = f"{d.code}_res"  # Results in "acc_res" (lowercase)

# BUG was here (table_view.py line 277):
disc_code = col_key.replace("_res", "").upper()  # "acc_res" -> "ACC" (WRONG!)
service.update_participant_result(startnr, "ACC", value)  # Service expects "acc"
```

## Fix
```python
# FIXED (table_view.py line 277):
disc_code = col_key.replace("_res", "")  # "acc_res" -> "acc" (CORRECT!)
service.update_participant_result(startnr, "acc", value)  # ✓ Matches service expectation
```

## Root Cause
The Discipline class has two fields:
- `code` (lowercase): Internal identifier used as dict keys
- `label` (uppercase): Display name for UI

The GUI was incorrectly uppercasing the code when it's already lowercase.

## Impact
- ✅ **Before fix**: Would have caused `KeyError` when trying to update results via inline editing
- ✅ **After fix**: Inline editing works correctly
- ✅ **Tests**: All 47 tests passing

## Files Modified
- `src/boomerang_score/app/components/table_view.py` (line 277)

## Convention Going Forward
**Always use lowercase for discipline codes:**
- Dict keys: `participant.disciplines["acc"]`
- Service methods: `service.update_participant_result(startnr, "acc", value)`
- GUI column keys: `"acc_res"`, `"acc_pts"`, `"acc_rank"`

**Use uppercase labels only for display:**
- Table headers: "ACC Res", "ACC Pts", "ACC Rank"
- User-facing text: "ACC" in menus, buttons, etc.

## Verification
```bash
$ PYTHONPATH=src python -m pytest test/ -q
...............................................                          [100%]
47 passed in 0.04s
```

All tests pass! ✅

# API Change: Startnumber as Immutable ID

## Summary

Refactored the participant identification system to use **startnumber** as the immutable participant ID instead of requiring callers to provide arbitrary IDs or using UUIDs internally.

## Benefits

✅ **Natural**: Startnumber is the natural identifier in sports competitions
✅ **Simple**: Integer lookup instead of string UUIDs
✅ **User-friendly**: Easy to reference ("update participant #5")
✅ **No duplication**: Startnumber and ID were redundant concepts
✅ **Cleaner API**: Callers don't need to generate/track IDs

## Breaking Changes

### Before (OLD API):
```python
# Caller had to provide participant_id
service.add_participant("some-uuid", "John Doe", 5, {"acc": 85.0})
service.update_participant_name("some-uuid", "Jane Doe")
service.update_participant_result("some-uuid", "acc", 90.0)
service.update_participant_startnumber("some-uuid", 6)  # Could change!

# Get participant
participant = competition.get_participant("some-uuid")
```

### After (NEW API):
```python
# Service returns the participant, startnumber is the ID
participant = service.add_participant("John Doe", 5, {"acc": 85.0})

# Use startnumber for all updates
service.update_participant_name(5, "Jane Doe")
service.update_participant_result(5, "acc", 90.0")
# update_startnumber() removed - startnumber is immutable!

# Get participant by startnumber
participant = competition.get_participant(5)
```

## Core Changes

### `Competition` class (models.py):
- `participants: dict[int, Participant]` (was `dict[str, Participant]`)
- `add_participant(participant: Participant)` (was `add_participant(participant_id, participant)`)
- `get_participant(startnumber: int)` (was `get_participant(participant_id: str)`)
- `remove_participant(startnumber: int)` (was `remove_participant(participant_id: str)`)
- `startnumber_exists(startnumber: int)` simplified (no `exclude_id` parameter needed)

### `CompetitionService` class:
- `add_participant(name, startnumber, results) -> Participant` (was `add_participant(pid, name, startnumber, results) -> Participant`)
- `update_participant_name(startnumber: int, name)` (was `update_participant_name(pid: str, name)`)
- `update_participant_result(startnumber: int, disc, result)` (was `update_participant_result(pid: str, disc, result)`)
- **REMOVED**: `update_participant_startnumber()` - startnumber is now immutable
- `recalculate_participant(startnumber: int)` (was `recalculate_participant(pid: str)`)

## Migration Guide

### For GUI Code:
```python
# OLD:
iid = self.tree.insert("", "end", values=...)
service.add_participant(iid, name, startnr, results)
service.update_participant_result(iid, "acc", 85.0)

# NEW:
participant = service.add_participant(name, startnr, results)
startnr = participant.startnumber
# Store startnr in tree item data or use as tree item ID
self.tree.insert("", "end", iid=str(startnr), values=...)
service.update_participant_result(startnr, "acc", 85.0)
```

### For CLI Code:
```python
# OLD:
pid = f"p{startnr}"
service.add_participant(pid, name, startnr, results)

# NEW:
participant = service.add_participant(name, startnr, results)
# startnumber is already the ID, no need to generate pid
```

### For Tests:
```python
# OLD:
service.add_participant("p1", "John", 1, {"acc": 50.0})
p = competition.get_participant("p1")

# NEW:
participant = service.add_participant("John", 1, {"acc": 50.0})
# OR:
service.add_participant("John", 1, {"acc": 50.0})
p = competition.get_participant(1)  # Use startnumber directly
```

## Design Decision: Immutability

**Startnumber cannot be changed after creation.** This is intentional:

### Rationale:
- In real competitions, bib numbers don't change mid-event
- Simplifies the data model (no need to update dict keys)
- Prevents identity confusion
- Edge case: If wrong startnumber entered, delete and re-add participant

### If you absolutely need to change startnumber:
```python
# Get participant data
old_participant = competition.get_participant(5)
name = old_participant.name
results = {code: old_participant.get_result(code)
           for code in ["acc", "aus", "mta", ...]}

# Remove old and add new
competition.remove_participant(5)
new_participant = service.add_participant(name, 6, results)  # New startnumber
```

## Files Modified

- ✅ `src/boomerang_score/core/models.py`
- ✅ `src/boomerang_score/services/competition_service.py`
- ⏳ `src/boomerang_score/app/rss_boomerang.py` (needs update)
- ⏳ `src/boomerang_score/app/adapter.py` (needs update)
- ⏳ `src/boomerang_score/cli.py` (needs update)
- ⏳ `test/core/test_models.py` (needs update)
- ⏳ `test/services/test_competition_service.py` (needs update)

## Next Steps

1. Update GUI to use startnumber as tree item ID
2. Update tests to use new API
3. Update CLI to use new API
4. Run full test suite
5. Update REFACTORING.md documentation

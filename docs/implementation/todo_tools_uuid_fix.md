# Todo Tools UUID Handling Fix

## Problem

The todo tools system in radbot experienced issues with UUID handling, particularly:

1. Tasks appeared to be added twice in the database
2. The system was unable to remove tasks, resulting in the error: `can't adapt type 'UUID'`

## Solution

The solution involved registering a UUID adapter for psycopg2 to properly handle UUID objects:

```python
# Register UUID adapter for psycopg2
psycopg2.extensions.register_adapter(uuid.UUID, lambda u: psycopg2.extensions.adapt(str(u)))
```

This adapter ensures UUID objects are properly converted to strings when sent to the PostgreSQL database.

Additionally, the remove_task function was enhanced with better error handling and debugging output.

## Implementation Details

The fix was implemented in:
- `db_tools.py`: Added UUID adapter registration
- `todo_tools.py`: Improved error handling in the remove_task function
- `db_tools.py`: Enhanced the _remove_task function to explicitly handle UUID to string conversion

## Testing

The fix was verified by successfully adding and removing tasks using the command-line interface.

## Notes for Future Development

When working with UUIDs in PostgreSQL:
1. Always ensure adapters are registered for proper type conversion
2. Consider using explicit string conversion when dealing with UUID values in SQL queries
3. Add thorough logging to track UUID conversions for debugging

# Todo Tools Enhanced Filtering

## Feature Overview

The todo tools system in radbot has been enhanced to automatically filter out completed tasks when listing todos, making it easier for users to focus on active tasks.

## Implementation Details

The enhancement modifies the `list_tasks` function in `todo_tools.py` to:

1. Add a new parameter `include_done: bool = False` which controls whether completed tasks are included in the results
2. By default, exclude all tasks with status 'done' unless explicitly requested
3. Maintain backward compatibility by respecting the `status_filter` parameter, which takes precedence if specified

## Logic Flow

The function now implements the following logic:

1. If `status_filter` is explicitly set to a specific value ('backlog', 'inprogress', or 'done'), it uses that filter as before
2. If `status_filter` is None and `include_done` is False (the default), it fetches all tasks but then filters out any with status 'done'
3. If `status_filter` is None but `include_done` is True, it returns all tasks without filtering

## Example Usage

```python
# Only see active tasks (default behavior)
agent.run("List my todo items for project radbot")

# Explicitly request to see completed tasks too
agent.run("List all my todo items including completed ones for project radbot")

# See only completed tasks
agent.run("List my completed tasks for project radbot")
```

## Advantages

This enhancement improves the user experience by:

1. Making the default behavior match user expectations (most users want to see active tasks)
2. Reducing cognitive load by not showing completed tasks that no longer require attention
3. Still allowing users to see completed tasks when needed for reference
4. Maintaining flexibility through the `status_filter` parameter for specific filtering needs

## Future Improvements

Potential future enhancements could include:

1. Adding a date filter to show tasks completed within a certain timeframe
2. Implementing task archiving for long-completed tasks
3. Adding statistics about completion rates and average time to completion

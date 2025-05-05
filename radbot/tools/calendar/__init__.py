"""Google Calendar integration for radbot."""

from radbot.tools.calendar.calendar_auth import (
    get_calendar_service,
    get_workspace_calendar_service,
)
from radbot.tools.calendar.calendar_manager import CalendarManager
from radbot.tools.calendar.calendar_tools import (
    list_calendar_events,
    create_calendar_event,
    update_calendar_event,
    delete_calendar_event,
    check_calendar_availability,
)

__all__ = [
    "get_calendar_service",
    "get_workspace_calendar_service",
    "CalendarManager",
    "list_calendar_events",
    "create_calendar_event",
    "update_calendar_event",
    "delete_calendar_event",
    "check_calendar_availability",
]
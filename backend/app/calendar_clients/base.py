from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class CalendarClient(ABC):

    @abstractmethod
    async def check_availability(
        self,
        date: str,
        timezone: str,
        workday_start: str,
        workday_end: str
    ) -> list[dict]:
        """
        Returns a list of available time slots for the given date.
        Each slot: {"start": "ISO8601", "end": "ISO8601"}
        """

    @abstractmethod
    async def create_event(
        self,
        start: str,
        name: str,
        email: str,
        title: str,
        description: str,
        timezone: str
    ) -> dict:
        """
        Creates a calendar event.
        Returns: {"event_id": str, "start": str, "end": str, "title": str}
        """

    @abstractmethod
    async def get_events_by_attendee(
        self,
        email: str,
        status: Optional[str] = "upcoming"
    ) -> list[dict]:
        """
        Returns calendar events for the given attendee email.
        Each event: {"event_id": str, "start": str, "end": str, "title": str, "description": str}
        """

    @abstractmethod
    async def cancel_event(self, event_id: str) -> bool:
        """Cancels/deletes the event. Returns True on success."""

    @abstractmethod
    async def reschedule_event(
        self,
        event_id: str,
        new_start: str,
        timezone: str
    ) -> dict:
        """
        Reschedules an event to new_start.
        Returns updated event: {"event_id": str, "start": str, "end": str}
        """

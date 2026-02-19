import json
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .base import CalendarClient

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarClient(CalendarClient):

    def __init__(self, service_account_json: str, calendar_id: str):
        """
        service_account_json: full JSON content of the service account key file
        calendar_id: Google Calendar ID (e.g., user@domain.com or calendar-specific ID)
        """
        self.calendar_id = calendar_id
        creds_info = json.loads(service_account_json)
        # Use service account credentials directly — no user impersonation.
        # The calendar must be shared with the service account's client_email.
        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=SCOPES
        )
        self._service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    async def check_availability(
        self,
        date: str,
        timezone: str,
        workday_start: str,
        workday_end: str
    ) -> list[dict]:
        tz = ZoneInfo(timezone)
        date_obj = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=tz)

        start_h, start_m = map(int, workday_start.split(":"))
        end_h, end_m = map(int, workday_end.split(":"))

        time_min = date_obj.replace(hour=start_h, minute=start_m, second=0)
        time_max = date_obj.replace(hour=end_h, minute=end_m, second=0)

        body = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "items": [{"id": self.calendar_id}],
            "timeZone": timezone,
        }

        try:
            freebusy = self._service.freebusy().query(body=body).execute()
            busy_slots = freebusy["calendars"].get(self.calendar_id, {}).get("busy", [])
        except HttpError as e:
            raise ValueError(f"Google Calendar API error: {e}")

        # Build available 1-hour slots avoiding busy times
        available = []
        current = time_min
        while current + timedelta(hours=1) <= time_max:
            slot_end = current + timedelta(hours=1)
            overlap = any(
                datetime.fromisoformat(b["start"]) < slot_end
                and datetime.fromisoformat(b["end"]) > current
                for b in busy_slots
            )
            if not overlap:
                available.append({
                    "start": current.isoformat(),
                    "end": slot_end.isoformat(),
                })
            current += timedelta(hours=1)

        return available

    async def create_event(
        self,
        start: str,
        name: str,
        email: str,
        title: str,
        description: str,
        timezone: str
    ) -> dict:
        start_dt = datetime.fromisoformat(start)
        end_dt = start_dt + timedelta(hours=1)

        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone},
            "attendees": [{"email": email, "displayName": name}],
        }

        try:
            event = self._service.events().insert(
                calendarId=self.calendar_id, body=event_body, sendUpdates="all"
            ).execute()
        except HttpError as e:
            raise ValueError(f"Google Calendar create error: {e}")

        return {
            "event_id": event["id"],
            "start": event["start"]["dateTime"],
            "end": event["end"]["dateTime"],
            "title": event.get("summary", title),
        }

    async def get_events_by_attendee(
        self,
        email: str,
        status: Optional[str] = "upcoming"
    ) -> list[dict]:
        now = datetime.utcnow().isoformat() + "Z"
        try:
            events_result = self._service.events().list(
                calendarId=self.calendar_id,
                timeMin=now,
                maxResults=50,
                singleEvents=True,
                orderBy="startTime",
            ).execute()
        except HttpError as e:
            raise ValueError(f"Google Calendar list error: {e}")

        events = events_result.get("items", [])
        attendee_events = []
        for e in events:
            attendees = e.get("attendees", [])
            if any(a.get("email", "").lower() == email.lower() for a in attendees):
                attendee_events.append({
                    "event_id": e["id"],
                    "start": e["start"].get("dateTime", e["start"].get("date", "")),
                    "end": e["end"].get("dateTime", e["end"].get("date", "")),
                    "title": e.get("summary", ""),
                    "description": e.get("description", ""),
                })
        return attendee_events

    async def cancel_event(self, event_id: str) -> bool:
        try:
            self._service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id,
                sendUpdates="all"
            ).execute()
            return True
        except HttpError as e:
            raise ValueError(f"Google Calendar cancel error: {e}")

    async def reschedule_event(
        self,
        event_id: str,
        new_start: str,
        timezone: str
    ) -> dict:
        try:
            event = self._service.events().get(
                calendarId=self.calendar_id, eventId=event_id
            ).execute()
        except HttpError as e:
            raise ValueError(f"Google Calendar get error: {e}")

        new_start_dt = datetime.fromisoformat(new_start)
        old_start = datetime.fromisoformat(event["start"]["dateTime"])
        old_end = datetime.fromisoformat(event["end"]["dateTime"])
        duration = old_end - old_start
        new_end_dt = new_start_dt + duration

        event["start"] = {"dateTime": new_start_dt.isoformat(), "timeZone": timezone}
        event["end"] = {"dateTime": new_end_dt.isoformat(), "timeZone": timezone}

        try:
            updated = self._service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event,
                sendUpdates="all"
            ).execute()
        except HttpError as e:
            raise ValueError(f"Google Calendar reschedule error: {e}")

        return {
            "event_id": updated["id"],
            "start": updated["start"]["dateTime"],
            "end": updated["end"]["dateTime"],
        }

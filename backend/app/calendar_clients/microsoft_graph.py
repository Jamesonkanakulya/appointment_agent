from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
import httpx

from .base import CalendarClient

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


class MicrosoftGraphClient(CalendarClient):

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        user_email: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.user_email = user_email
        self._token: str | None = None

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TOKEN_URL.format(tenant_id=self.tenant_id),
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                },
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
        return self._token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

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
            "schedules": [self.user_email],
            "startTime": {"dateTime": time_min.isoformat(), "timeZone": timezone},
            "endTime": {"dateTime": time_max.isoformat(), "timeZone": timezone},
            "availabilityViewInterval": 60,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRAPH_BASE}/users/{self.user_email}/calendar/getSchedule",
                json=body,
                headers=await self._headers()
            )
            resp.raise_for_status()
            data = resp.json()

        schedules = data.get("value", [])
        if not schedules:
            return []

        availability_view = schedules[0].get("availabilityView", "")
        # availabilityView is a string of digits where 0=free, 2=busy, per interval
        available = []
        current = time_min
        for char in availability_view:
            slot_end = current + timedelta(hours=1)
            if char == "0":
                available.append({"start": current.isoformat(), "end": slot_end.isoformat()})
            current = slot_end
            if current >= time_max:
                break

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

        body = {
            "subject": title,
            "body": {"contentType": "Text", "content": description},
            "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone},
            "attendees": [
                {
                    "emailAddress": {"address": email, "name": name},
                    "type": "required"
                }
            ],
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GRAPH_BASE}/users/{self.user_email}/events",
                json=body,
                headers=await self._headers()
            )
            resp.raise_for_status()
            event = resp.json()

        return {
            "event_id": event["id"],
            "start": event["start"]["dateTime"],
            "end": event["end"]["dateTime"],
            "title": event.get("subject", title),
        }

    async def get_events_by_attendee(
        self,
        email: str,
        status: Optional[str] = "upcoming"
    ) -> list[dict]:
        now = datetime.utcnow().isoformat() + "Z"
        url = (
            f"{GRAPH_BASE}/users/{self.user_email}/events"
            f"?$filter=start/dateTime ge '{now}'"
            f"&$orderby=start/dateTime"
            f"&$top=50"
        )

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=await self._headers())
            resp.raise_for_status()
            data = resp.json()

        events = data.get("value", [])
        attendee_events = []
        for e in events:
            attendees = e.get("attendees", [])
            if any(
                a.get("emailAddress", {}).get("address", "").lower() == email.lower()
                for a in attendees
            ):
                attendee_events.append({
                    "event_id": e["id"],
                    "start": e["start"]["dateTime"],
                    "end": e["end"]["dateTime"],
                    "title": e.get("subject", ""),
                    "description": e.get("body", {}).get("content", ""),
                })
        return attendee_events

    async def cancel_event(self, event_id: str) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{GRAPH_BASE}/users/{self.user_email}/events/{event_id}",
                headers=await self._headers()
            )
            resp.raise_for_status()
        return True

    async def reschedule_event(
        self,
        event_id: str,
        new_start: str,
        timezone: str
    ) -> dict:
        # Get current event to preserve duration
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_BASE}/users/{self.user_email}/events/{event_id}",
                headers=await self._headers()
            )
            resp.raise_for_status()
            event = resp.json()

        old_start = datetime.fromisoformat(event["start"]["dateTime"])
        old_end = datetime.fromisoformat(event["end"]["dateTime"])
        duration = old_end - old_start
        new_start_dt = datetime.fromisoformat(new_start)
        new_end_dt = new_start_dt + duration

        patch_body = {
            "start": {"dateTime": new_start_dt.isoformat(), "timeZone": timezone},
            "end": {"dateTime": new_end_dt.isoformat(), "timeZone": timezone},
        }

        async with httpx.AsyncClient() as client:
            resp = await client.patch(
                f"{GRAPH_BASE}/users/{self.user_email}/events/{event_id}",
                json=patch_body,
                headers=await self._headers()
            )
            resp.raise_for_status()
            updated = resp.json()

        return {
            "event_id": updated["id"],
            "start": updated["start"]["dateTime"],
            "end": updated["end"]["dateTime"],
        }

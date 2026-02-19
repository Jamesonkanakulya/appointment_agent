"""
Cal.com API v1 client.
Uses ?apiKey=xxx query parameter authentication.
Base URL: https://api.cal.com/v1
"""
import logging
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

CALCOM_BASE = "https://api.cal.com/v1"


class CalComClient:
    def __init__(self, api_key: str, event_type_id: int):
        self.api_key = api_key
        self.event_type_id = event_type_id

    def _params(self, extra: dict | None = None) -> dict:
        p = {"apiKey": self.api_key}
        if extra:
            p.update(extra)
        return p

    # ─── Availability ────────────────────────────────────────────────────────

    async def check_availability(self, date: str, tz: str = "UTC") -> list[dict]:
        """
        Return available slots for *date* (YYYY-MM-DD).
        Calls GET /slots/available and returns [{start, end}] pairs.
        """
        # Build startTime / endTime spanning the whole day in UTC
        start_time = f"{date}T00:00:00.000Z"
        end_time = f"{date}T23:59:59.000Z"

        params = self._params({
            "startTime": start_time,
            "endTime": end_time,
            "eventTypeId": self.event_type_id,
            "timeZone": tz,
        })

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(f"{CALCOM_BASE}/slots/available", params=params)
            resp.raise_for_status()
            data = resp.json()

        # Response: {"slots": {"2024-01-15": [{"time": "ISO"}, ...]}}
        slots_by_date = data.get("slots", {})
        result = []
        for day_slots in slots_by_date.values():
            for slot in day_slots:
                slot_start = slot.get("time") or slot.get("startTime", "")
                if not slot_start:
                    continue
                # Cal.com returns start time; assume 30-min duration by default
                try:
                    dt_start = datetime.fromisoformat(slot_start.replace("Z", "+00:00"))
                    dt_end = dt_start + timedelta(minutes=30)
                    result.append({
                        "start": dt_start.isoformat(),
                        "end": dt_end.isoformat(),
                    })
                except Exception:
                    result.append({"start": slot_start, "end": slot_start})
        return result

    # ─── Create Booking ───────────────────────────────────────────────────────

    async def create_booking(
        self,
        start: str,
        name: str,
        email: str,
        title: str = "",
        tz: str = "UTC",
    ) -> dict:
        """
        Create a booking and return {uid, id, start, end, title}.
        """
        body = {
            "eventTypeId": self.event_type_id,
            "start": start,
            "responses": {
                "name": name,
                "email": email,
            },
            "timeZone": tz,
            "language": "en",
            "metadata": {},
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{CALCOM_BASE}/bookings",
                params=self._params(),
                json=body,
            )
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Cal.com create_booking error: {e.response.text}")
                raise

        data = resp.json()
        return {
            "uid": data.get("uid", ""),
            "id": data.get("id", 0),
            "start": data.get("startTime", start),
            "end": data.get("endTime", ""),
            "title": data.get("title", title),
        }

    # ─── Get Bookings ─────────────────────────────────────────────────────────

    async def get_bookings_by_email(self, email: str) -> list[dict]:
        """
        Fetch all ACCEPTED/upcoming bookings and filter by attendee email.
        Returns [{uid, id, title, start, end, status, attendee_name, attendee_email}]
        """
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{CALCOM_BASE}/bookings",
                params=self._params({"status": "upcoming"}),
            )
            resp.raise_for_status()
            data = resp.json()

        bookings = data.get("bookings", [])
        result = []
        for b in bookings:
            attendees = b.get("attendees", [])
            match = any(
                a.get("email", "").lower() == email.lower()
                for a in attendees
            )
            if not match:
                continue

            attendee = next(
                (a for a in attendees if a.get("email", "").lower() == email.lower()),
                {}
            )
            result.append({
                "uid": b.get("uid", ""),
                "id": b.get("id", 0),
                "title": b.get("title", ""),
                "start": b.get("startTime", ""),
                "end": b.get("endTime", ""),
                "status": b.get("status", ""),
                "attendee_name": attendee.get("name", ""),
                "attendee_email": attendee.get("email", ""),
            })
        return result

    # ─── Cancel Booking ───────────────────────────────────────────────────────

    async def cancel_booking(self, uid: str, reason: str = "") -> bool:
        """
        Cancel a booking by its uid.
        Internally: find numeric id via GET /bookings, then DELETE /bookings/{id}.
        """
        booking_id = await self._get_numeric_id(uid)
        if booking_id is None:
            # Try DELETE directly with uid
            booking_id = uid

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(
                f"{CALCOM_BASE}/bookings/{booking_id}",
                params=self._params({"cancellationReason": reason} if reason else {}),
            )
            if resp.status_code == 200 or resp.status_code == 204:
                return True
            # Some versions use POST /bookings/cancel
            resp2 = await client.post(
                f"{CALCOM_BASE}/bookings/cancel",
                params=self._params(),
                json={"id": booking_id, "cancellationReason": reason},
            )
            return resp2.status_code in (200, 204)

    # ─── Reschedule Booking ───────────────────────────────────────────────────

    async def reschedule_booking(self, uid: str, new_start: str) -> dict:
        """
        Reschedule a booking to new_start (ISO 8601).
        Uses PATCH /bookings/{id} if supported, otherwise cancel + recreate.
        Returns {uid, start, end}.
        """
        booking_id = await self._get_numeric_id(uid)

        if booking_id is not None:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.patch(
                    f"{CALCOM_BASE}/bookings/{booking_id}",
                    params=self._params(),
                    json={"start": new_start},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "uid": data.get("uid", uid),
                        "start": data.get("startTime", new_start),
                        "end": data.get("endTime", ""),
                    }

        # Fallback: cancel + create new booking (get original attendee info first)
        original = await self._get_booking_by_uid(uid)
        if original:
            await self.cancel_booking(uid, reason="Rescheduled by agent")
            attendees = original.get("attendees", [{}])
            attendee = attendees[0] if attendees else {}
            new_booking = await self.create_booking(
                start=new_start,
                name=attendee.get("name", "Guest"),
                email=attendee.get("email", ""),
                title=original.get("title", ""),
                tz=attendee.get("timeZone", "UTC"),
            )
            return new_booking

        return {"uid": uid, "start": new_start, "end": ""}

    # ─── Internal helpers ─────────────────────────────────────────────────────

    async def _get_all_bookings(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{CALCOM_BASE}/bookings",
                params=self._params(),
            )
            resp.raise_for_status()
            return resp.json().get("bookings", [])

    async def _get_booking_by_uid(self, uid: str) -> dict | None:
        bookings = await self._get_all_bookings()
        for b in bookings:
            if b.get("uid") == uid:
                return b
        return None

    async def _get_numeric_id(self, uid: str) -> int | None:
        b = await self._get_booking_by_uid(uid)
        return b.get("id") if b else None

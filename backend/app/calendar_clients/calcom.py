"""
Cal.com API v2 client.
Auth: Authorization: Bearer <api_key> header + cal-api-version header.
Base URL: https://api.cal.com/v2
"""
import logging
from datetime import datetime, timedelta

import httpx

logger = logging.getLogger(__name__)

CALCOM_BASE = "https://api.cal.com/v2"


class CalComClient:
    def __init__(self, api_key: str, event_type_id: int):
        self.api_key = api_key
        self.event_type_id = event_type_id

    def _headers(self, api_version: str = "2024-08-13") -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "cal-api-version": api_version,
            "Content-Type": "application/json",
        }

    # ─── Availability ────────────────────────────────────────────────────────

    async def check_availability(self, date: str, tz: str = "UTC") -> list[dict]:
        """
        Return available slots for *date* (YYYY-MM-DD).
        GET /v2/slots?start=...&end=...&eventTypeId=...&timeZone=...
        Returns [{start, end}] pairs.
        """
        start_time = f"{date}T00:00:00.000Z"
        end_time = f"{date}T23:59:59.000Z"

        params = {
            "start": start_time,
            "end": end_time,
            "eventTypeId": self.event_type_id,
            "timeZone": tz,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{CALCOM_BASE}/slots",
                params=params,
                headers=self._headers("2024-09-04"),
            )
            if not resp.is_success:
                logger.error(f"Cal.com check_availability error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            data = resp.json()

        # Response: {"status":"success","data":{"2026-02-23":[{"start":"ISO"},...]}}
        slots_by_date = data.get("data", {})
        result = []
        for day_slots in slots_by_date.values():
            for slot in day_slots:
                slot_start = slot.get("start", "")
                if not slot_start:
                    continue
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
        Create a booking via POST /v2/bookings.
        Returns {uid, id, start, end, title}.
        """
        body = {
            "eventTypeId": self.event_type_id,
            "start": start,
            "attendee": {
                "name": name,
                "email": email,
                "timeZone": tz,
            },
            "metadata": {},
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{CALCOM_BASE}/bookings",
                headers=self._headers("2024-08-13"),
                json=body,
            )
            if not resp.is_success:
                logger.error(f"Cal.com create_booking error {resp.status_code}: {resp.text}")
            resp.raise_for_status()

        data = resp.json().get("data", {})
        return {
            "uid": data.get("uid", ""),
            "id": data.get("id", 0),
            "start": data.get("start", start),
            "end": data.get("end", ""),
            "title": data.get("title", title),
        }

    # ─── Get Bookings ─────────────────────────────────────────────────────────

    async def get_bookings_by_email(self, email: str) -> list[dict]:
        """
        Fetch upcoming bookings filtered by attendee email.
        GET /v2/bookings?status=upcoming
        Returns [{uid, id, title, start, end, status, attendee_name, attendee_email}]
        """
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{CALCOM_BASE}/bookings",
                params={"status": "upcoming"},
                headers=self._headers("2024-11-18"),
            )
            if not resp.is_success:
                logger.error(f"Cal.com get_bookings error {resp.status_code}: {resp.text}")
            resp.raise_for_status()
            data = resp.json()

        bookings = data.get("data", {}).get("bookings", [])
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
                "start": b.get("start", b.get("startTime", "")),
                "end": b.get("end", b.get("endTime", "")),
                "status": b.get("status", ""),
                "attendee_name": attendee.get("name", ""),
                "attendee_email": attendee.get("email", ""),
            })
        return result

    # ─── Cancel Booking ───────────────────────────────────────────────────────

    async def cancel_booking(self, uid: str, reason: str = "") -> bool:
        """
        Cancel a booking via POST /v2/bookings/{uid}/cancel.
        """
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{CALCOM_BASE}/bookings/{uid}/cancel",
                headers=self._headers("2024-08-13"),
                json={"cancellationReason": reason} if reason else {},
            )
            if resp.status_code in (200, 201, 204):
                return True
            logger.error(f"Cal.com cancel_booking error {resp.status_code}: {resp.text}")
            return False

    # ─── Reschedule Booking ───────────────────────────────────────────────────

    async def reschedule_booking(self, uid: str, new_start: str) -> dict:
        """
        Reschedule via POST /v2/bookings/{uid}/reschedule.
        Returns {uid, start, end}.
        """
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{CALCOM_BASE}/bookings/{uid}/reschedule",
                headers=self._headers("2024-08-13"),
                json={"start": new_start},
            )
            if resp.is_success:
                data = resp.json().get("data", {})
                return {
                    "uid": data.get("uid", uid),
                    "start": data.get("start", new_start),
                    "end": data.get("end", ""),
                }
            logger.error(f"Cal.com reschedule error {resp.status_code}: {resp.text}")

        # Fallback: cancel + recreate
        original = await self._get_booking_by_uid(uid)
        if original:
            attendees = original.get("attendees", [{}])
            attendee = attendees[0] if attendees else {}
            await self.cancel_booking(uid, reason="Rescheduled by agent")
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
                headers=self._headers("2024-11-18"),
            )
            resp.raise_for_status()
            return resp.json().get("data", {}).get("bookings", [])

    async def _get_booking_by_uid(self, uid: str) -> dict | None:
        bookings = await self._get_all_bookings()
        for b in bookings:
            if b.get("uid") == uid:
                return b
        return None

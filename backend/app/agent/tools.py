"""
Tool dispatcher — routes agent tool calls to calendar clients or DB operations.
"""
import json
import random
from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Instance, GuestRecord
from ..encryption import decrypt
from ..calendar_clients.google_calendar import GoogleCalendarClient
from ..calendar_clients.microsoft_graph import MicrosoftGraphClient
from ..calendar_clients.base import CalendarClient


def _get_calendar_client(instance: Instance) -> CalendarClient:
    if instance.calendar_provider == "google":
        if not instance.google_service_account_json or not instance.google_calendar_id:
            raise ValueError("Google Calendar credentials not configured for this instance.")
        sa_json = decrypt(instance.google_service_account_json)
        return GoogleCalendarClient(sa_json, instance.google_calendar_id)
    elif instance.calendar_provider == "microsoft":
        if not all([instance.microsoft_client_id, instance.microsoft_client_secret,
                    instance.microsoft_tenant_id, instance.microsoft_user_email]):
            raise ValueError("Microsoft 365 credentials not fully configured for this instance.")
        secret = decrypt(instance.microsoft_client_secret)
        return MicrosoftGraphClient(
            client_id=instance.microsoft_client_id,
            client_secret=secret,
            tenant_id=instance.microsoft_tenant_id,
            user_email=instance.microsoft_user_email,
        )
    else:
        raise ValueError(f"Unknown calendar provider: {instance.calendar_provider}")


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    instance: Instance,
    db: AsyncSession
) -> Any:
    """Route a tool call to the appropriate implementation."""
    try:
        if tool_name == "check_availability":
            return await _check_availability(tool_input, instance)
        elif tool_name == "create_booking":
            return await _create_booking(tool_input, instance, db)
        elif tool_name == "get_booking_information":
            return await _get_booking_information(tool_input, instance)
        elif tool_name == "cancel_booking":
            return await _cancel_booking(tool_input, instance, db)
        elif tool_name == "reschedule_booking":
            return await _reschedule_booking(tool_input, instance, db)
        elif tool_name == "add_guest_record":
            return await _add_guest_record(tool_input, instance, db)
        elif tool_name == "search_guest_record":
            return await _search_guest_record(tool_input, instance, db)
        elif tool_name == "update_guest_record":
            return await _update_guest_record(tool_input, instance, db)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


async def _check_availability(inputs: dict, instance: Instance) -> dict:
    client = _get_calendar_client(instance)
    slots = await client.check_availability(
        date=inputs["date"],
        timezone=instance.timezone,
        workday_start=instance.workday_start,
        workday_end=instance.workday_end,
    )
    if not slots:
        return {"available": False, "message": "No available slots on this date."}
    return {"available": True, "slots": slots}


async def _create_booking(inputs: dict, instance: Instance, db: AsyncSession) -> dict:
    client = _get_calendar_client(instance)
    event = await client.create_event(
        start=inputs["start"],
        name=inputs["name"],
        email=inputs["email"],
        title=inputs["title"],
        description=inputs["description"],
        timezone=instance.timezone,
    )
    return {"success": True, "event_id": event["event_id"], "start": event["start"], "end": event["end"]}


async def _get_booking_information(inputs: dict, instance: Instance) -> dict:
    client = _get_calendar_client(instance)
    events = await client.get_events_by_attendee(email=inputs["email"])
    if not events:
        return {"bookings": [], "message": "No upcoming bookings found for this email."}
    return {"bookings": events}


async def _cancel_booking(inputs: dict, instance: Instance, db: AsyncSession) -> dict:
    client = _get_calendar_client(instance)
    success = await client.cancel_event(event_id=inputs["event_id"])
    if success:
        # Update guest record status
        await db.execute(
            update(GuestRecord)
            .where(
                GuestRecord.instance_id == instance.id,
                GuestRecord.email == inputs["email"],
                GuestRecord.calendar_event_id == inputs["event_id"]
            )
            .values(status="Canceled", updated_at=datetime.utcnow())
        )
        await db.commit()
    return {"success": success}


async def _reschedule_booking(inputs: dict, instance: Instance, db: AsyncSession) -> dict:
    client = _get_calendar_client(instance)
    updated = await client.reschedule_event(
        event_id=inputs["event_id"],
        new_start=inputs["new_start"],
        timezone=instance.timezone,
    )
    # Generate new PIN and update record
    new_pin = await _generate_unique_pin(instance, db)
    new_booking_time = datetime.fromisoformat(updated["start"])

    await db.execute(
        update(GuestRecord)
        .where(
            GuestRecord.instance_id == instance.id,
            GuestRecord.email == inputs["email"],
            GuestRecord.calendar_event_id == inputs["event_id"]
        )
        .values(
            status="Rescheduled",
            pin_code=new_pin,
            booking_time=new_booking_time,
            updated_at=datetime.utcnow()
        )
    )
    await db.commit()
    return {"success": True, "new_pin": new_pin, "new_start": updated["start"], "new_end": updated["end"]}


async def _add_guest_record(inputs: dict, instance: Instance, db: AsyncSession) -> dict:
    booking_time = None
    if inputs.get("booking_time"):
        try:
            booking_time = datetime.fromisoformat(inputs["booking_time"])
        except ValueError:
            pass

    record = GuestRecord(
        instance_id=instance.id,
        name=inputs.get("name"),
        email=inputs["email"],
        pin_code=inputs["pin_code"],
        booking_time=booking_time,
        status="Active",
        meeting_title=inputs.get("meeting_title"),
        calendar_event_id=inputs.get("calendar_event_id"),
    )
    db.add(record)
    await db.commit()
    return {"success": True, "id": record.id}


async def _search_guest_record(inputs: dict, instance: Instance, db: AsyncSession) -> dict:
    result = await db.execute(
        select(GuestRecord)
        .where(
            GuestRecord.instance_id == instance.id,
            GuestRecord.email == inputs["email"],
        )
        .order_by(GuestRecord.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"found": False, "message": "No guest record found for this email."}
    return {
        "found": True,
        "name": record.name,
        "email": record.email,
        "pin_code": record.pin_code,
        "booking_time": record.booking_time.isoformat() if record.booking_time else None,
        "status": record.status,
        "meeting_title": record.meeting_title,
        "calendar_event_id": record.calendar_event_id,
    }


async def _update_guest_record(inputs: dict, instance: Instance, db: AsyncSession) -> dict:
    result = await db.execute(
        select(GuestRecord)
        .where(
            GuestRecord.instance_id == instance.id,
            GuestRecord.email == inputs["email"],
        )
        .order_by(GuestRecord.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"success": False, "message": "Guest record not found."}

    if inputs.get("status"):
        record.status = inputs["status"]
    if inputs.get("pin_code"):
        record.pin_code = inputs["pin_code"]
    if inputs.get("booking_time"):
        try:
            record.booking_time = datetime.fromisoformat(inputs["booking_time"])
        except ValueError:
            pass
    if inputs.get("calendar_event_id"):
        record.calendar_event_id = inputs["calendar_event_id"]
    record.updated_at = datetime.utcnow()

    await db.commit()
    return {"success": True}


async def _generate_unique_pin(instance: Instance, db: AsyncSession) -> str:
    """Generate a random 4-digit PIN not already in use for this instance."""
    for _ in range(20):
        pin = str(random.randint(1000, 9999))
        result = await db.execute(
            select(GuestRecord).where(
                GuestRecord.instance_id == instance.id,
                GuestRecord.pin_code == pin,
                GuestRecord.status == "Active"
            )
        )
        if not result.scalar_one_or_none():
            return pin
    # Fallback: return random pin (collision extremely unlikely after 20 tries)
    return str(random.randint(1000, 9999))

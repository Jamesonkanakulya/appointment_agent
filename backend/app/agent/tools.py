"""
Tool dispatcher for the appointment booking agent.
Each function maps to one of the 10 tools defined in tool_schemas.py.
Cal.com is used for all calendar operations.
Guest records (PIN, status) are stored in PostgreSQL.
"""
import logging
from datetime import datetime

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Instance, GuestRecord, GlobalSettings
from ..encryption import decrypt
from ..calendar_clients.calcom import CalComClient

logger = logging.getLogger(__name__)


# ─── Cal.com client factory ───────────────────────────────────────────────────

def _get_calcom_client(instance: Instance) -> CalComClient:
    if not instance.calcom_api_key:
        raise RuntimeError("Cal.com API key not configured for this instance.")
    if not instance.calcom_event_type_id:
        raise RuntimeError("Cal.com Event Type ID not configured for this instance.")
    api_key = decrypt(instance.calcom_api_key)
    return CalComClient(api_key=api_key, event_type_id=instance.calcom_event_type_id)


# ─── Main dispatcher ──────────────────────────────────────────────────────────

async def execute_tool(
    tool_name: str,
    tool_input: dict,
    instance: Instance,
    db: AsyncSession,
) -> dict:
    """Route a tool call to the appropriate implementation."""
    handlers = {
        "check_availability":      _check_availability,
        "create_booking":          _create_booking,
        "get_booking_information": _get_booking_information,
        "cancel_booking":          _cancel_booking,
        "reschedule_booking":      _reschedule_booking,
        "search_guest":            _search_guest,
        "add_to_list":             _add_to_list,
        "update_the_list":         _update_the_list,
        "search_all_guests":       _search_all_guests,
        "send_booking_email":      _send_booking_email,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return await handler(tool_input, instance, db)
    except Exception as e:
        logger.error(f"Tool {tool_name} raised exception: {e}", exc_info=True)
        return {"error": str(e)}


# ─── Cal.com tools ────────────────────────────────────────────────────────────

async def _check_availability(args: dict, instance: Instance, db: AsyncSession) -> dict:
    date = args.get("date", "")
    if not date:
        return {"error": "date is required"}
    client = _get_calcom_client(instance)
    slots = await client.check_availability(date=date, tz=instance.timezone)
    if not slots:
        return {"available": False, "slots": [], "message": f"No available slots on {date}"}
    return {"available": True, "slots": slots, "date": date}


async def _create_booking(args: dict, instance: Instance, db: AsyncSession) -> dict:
    start = args.get("start", "")
    name = args.get("name", "")
    email = args.get("email", "")
    title = args.get("title", "Appointment")

    if not all([start, name, email]):
        return {"error": "start, name, and email are required"}

    client = _get_calcom_client(instance)
    booking = await client.create_booking(
        start=start,
        name=name,
        email=email,
        title=title,
        tz=instance.timezone,
    )
    return {
        "success": True,
        "uid": booking.get("uid", ""),
        "id": booking.get("id", 0),
        "start": booking.get("start", start),
        "end": booking.get("end", ""),
        "title": booking.get("title", title),
    }


async def _get_booking_information(args: dict, instance: Instance, db: AsyncSession) -> dict:
    email = args.get("email", "")
    if not email:
        return {"error": "email is required"}

    client = _get_calcom_client(instance)
    bookings = await client.get_bookings_by_email(email=email)

    if not bookings:
        return {"found": False, "bookings": [], "message": f"No upcoming bookings found for {email}"}

    return {"found": True, "bookings": bookings}


async def _cancel_booking(args: dict, instance: Instance, db: AsyncSession) -> dict:
    uid = args.get("uid", "")
    reason = args.get("reason", "User requested cancellation")

    if not uid:
        return {"error": "uid is required"}

    client = _get_calcom_client(instance)
    success = await client.cancel_booking(uid=uid, reason=reason)
    return {"success": success, "uid": uid}


async def _reschedule_booking(args: dict, instance: Instance, db: AsyncSession) -> dict:
    uid = args.get("uid", "")
    new_start = args.get("new_start", "")

    if not uid or not new_start:
        return {"error": "uid and new_start are required"}

    client = _get_calcom_client(instance)
    result = await client.reschedule_booking(uid=uid, new_start=new_start)
    return {
        "success": True,
        "uid": result.get("uid", uid),
        "new_start": result.get("start", new_start),
        "new_end": result.get("end", ""),
    }


# ─── Database / guest record tools ───────────────────────────────────────────

async def _search_guest(args: dict, instance: Instance, db: AsyncSession) -> dict:
    email = args.get("email", "").lower().strip()
    if not email:
        return {"found": False, "error": "email is required"}

    result = await db.execute(
        select(GuestRecord)
        .where(GuestRecord.instance_id == instance.id)
        .where(GuestRecord.email.ilike(email))
        .order_by(GuestRecord.updated_at.desc())
    )
    record = result.scalars().first()
    if not record:
        return {"found": False, "message": f"No guest record found for {email}"}

    return {
        "found": True,
        "Name": record.name or "",
        "Email": record.email,
        "code": record.pin_code,  # Named 'code' to match system prompt examples
        "Booking time": record.booking_time.isoformat() if record.booking_time else "",
        "Status": record.status,
        "meeting_title": record.meeting_title or "",
        "booking_uid": record.calendar_event_id or "",
    }


async def _add_to_list(args: dict, instance: Instance, db: AsyncSession) -> dict:
    name = args.get("name", "")
    email = args.get("email", "").lower().strip()
    pin_code = str(args.get("pin_code", ""))
    booking_time_str = args.get("booking_time", "")
    status = args.get("status", "Active")
    meeting_title = args.get("meeting_title", "")
    booking_uid = args.get("booking_uid", "")

    if not email or not pin_code:
        return {"success": False, "error": "email and pin_code are required"}

    booking_time = None
    if booking_time_str:
        try:
            booking_time = datetime.fromisoformat(booking_time_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    record = GuestRecord(
        instance_id=instance.id,
        name=name,
        email=email,
        pin_code=pin_code,
        booking_time=booking_time,
        status=status,
        meeting_title=meeting_title,
        calendar_event_id=booking_uid,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return {"success": True, "id": record.id}


async def _update_the_list(args: dict, instance: Instance, db: AsyncSession) -> dict:
    email = args.get("email", "").lower().strip()
    status = args.get("status", "")
    pin_code = args.get("pin_code")
    booking_time_str = args.get("booking_time")
    meeting_title = args.get("meeting_title")
    booking_uid = args.get("booking_uid")

    if not email:
        return {"success": False, "error": "email is required"}

    result = await db.execute(
        select(GuestRecord)
        .where(GuestRecord.instance_id == instance.id)
        .where(GuestRecord.email.ilike(email))
        .order_by(GuestRecord.updated_at.desc())
    )
    record = result.scalars().first()
    if not record:
        return {"success": False, "error": f"No guest record found for {email}"}

    if status:
        record.status = status
    if pin_code is not None:
        record.pin_code = str(pin_code)
    if booking_time_str is not None:
        try:
            record.booking_time = datetime.fromisoformat(booking_time_str.replace("Z", "+00:00"))
        except ValueError:
            pass
    if meeting_title is not None:
        record.meeting_title = meeting_title
    if booking_uid is not None:
        record.calendar_event_id = booking_uid

    record.updated_at = datetime.utcnow()
    await db.commit()
    return {"success": True, "email": email, "status": record.status}


async def _search_all_guests(args: dict, instance: Instance, db: AsyncSession) -> dict:
    result = await db.execute(
        select(GuestRecord).where(GuestRecord.instance_id == instance.id)
    )
    records = result.scalars().all()
    guests = [
        {
            "name": r.name or "",
            "email": r.email,
            "pin_code": r.pin_code,
            "status": r.status,
        }
        for r in records
    ]
    return {"guests": guests, "count": len(guests)}


# ─── Email tool ───────────────────────────────────────────────────────────────

async def _send_booking_email(args: dict, instance: Instance, db: AsyncSession) -> dict:
    guest_name = args.get("guest_name", "")
    email_address = args.get("email_address", "")
    email_content = args.get("email_content", {})
    subject = email_content.get("subject", "Booking Notification")
    body = email_content.get("body", "")

    if not email_address:
        return {"success": False, "error": "email_address is required"}

    # Load SMTP settings from global settings
    gs_result = await db.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
    gs = gs_result.scalar_one_or_none()

    if not gs or not gs.smtp_host or not gs.smtp_user or not gs.smtp_password:
        logger.info(f"SMTP not configured — skipping email to {email_address}")
        return {
            "success": True,
            "note": "SMTP not configured in Global Settings. Email not sent.",
            "would_have_sent_to": email_address,
            "subject": subject,
        }

    smtp_password = decrypt(gs.smtp_password)
    from_email = gs.smtp_from_email or gs.smtp_user

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = email_address
    msg.attach(MIMEText(body, "plain"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=gs.smtp_host,
            port=gs.smtp_port or 587,
            username=gs.smtp_user,
            password=smtp_password,
            start_tls=True,
        )
        logger.info(f"Email sent to {email_address}: {subject}")
        return {"success": True, "sent_to": email_address, "subject": subject}
    except Exception as e:
        logger.error(f"Failed to send email to {email_address}: {e}")
        return {"success": False, "error": f"Failed to send email: {str(e)}"}

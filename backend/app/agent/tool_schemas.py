"""
LiteLLM tool schemas for the appointment booking agent.
All tools are provider-agnostic — the tools.py dispatcher handles implementation.
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": (
                "Check available appointment slots for a given date. "
                "Returns a list of free time slots during business hours."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to check in YYYY-MM-DD format (e.g., 2026-02-20)"
                    }
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_booking",
            "description": (
                "Create a new appointment booking on the calendar and record the guest. "
                "A unique 4-digit PIN is generated and stored for future verification. "
                "ONLY call this after confirming availability."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format (e.g., 2026-02-20T10:00:00+04:00)"
                    },
                    "name": {"type": "string", "description": "Guest's full name"},
                    "email": {"type": "string", "description": "Guest's email address"},
                    "title": {"type": "string", "description": "Meeting title"},
                    "description": {"type": "string", "description": "Meeting description"}
                },
                "required": ["start", "name", "email", "title", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_booking_information",
            "description": (
                "Retrieve existing upcoming bookings for a guest by their email address. "
                "Returns booking details including event_id (needed for cancel/reschedule)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Guest's email address"}
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_booking",
            "description": (
                "Cancel an existing booking. Requires the event_id from get_booking_information. "
                "PIN must be verified BEFORE calling this tool."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "Calendar event ID from get_booking_information"
                    },
                    "email": {"type": "string", "description": "Guest's email address"},
                    "reason": {
                        "type": "string",
                        "description": "Reason for cancellation (default: 'User requested cancellation')"
                    }
                },
                "required": ["event_id", "email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_booking",
            "description": (
                "Reschedule an existing booking to a new time. "
                "Requires the event_id from get_booking_information. "
                "PIN must be verified BEFORE calling this tool. "
                "A new unique PIN is generated after successful reschedule."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "string",
                        "description": "Calendar event ID from get_booking_information"
                    },
                    "email": {"type": "string", "description": "Guest's email address"},
                    "new_start": {
                        "type": "string",
                        "description": "New start time in ISO 8601 format"
                    }
                },
                "required": ["event_id", "email", "new_start"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_guest_record",
            "description": (
                "Add a new guest record to the database with a PIN code. "
                "ONLY call this when creating a NEW booking (not for cancel/reschedule). "
                "Generate a random 4-digit PIN and pass it here."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Guest's full name"},
                    "email": {"type": "string", "description": "Guest's email address"},
                    "pin_code": {
                        "type": "string",
                        "description": "4-digit PIN code (e.g., '4821'). Must be unique."
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "Booking time in ISO 8601 format"
                    },
                    "meeting_title": {"type": "string", "description": "Meeting title"},
                    "calendar_event_id": {
                        "type": "string",
                        "description": "Calendar event ID returned by create_booking"
                    }
                },
                "required": ["name", "email", "pin_code", "booking_time", "meeting_title", "calendar_event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_guest_record",
            "description": (
                "Look up a guest record by email address. "
                "Returns the guest's name, PIN code (for internal verification), "
                "and booking status. ALWAYS call this before cancel/reschedule to get the PIN."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Guest's email address"}
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_guest_record",
            "description": (
                "Update an existing guest record (status, PIN, booking time). "
                "Use for cancel (status='Canceled') and reschedule (new booking_time + new PIN). "
                "Do NOT use for new bookings — use add_guest_record instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Guest's email address (used to find the record)"},
                    "status": {
                        "type": "string",
                        "enum": ["Active", "Canceled", "Rescheduled"],
                        "description": "New status"
                    },
                    "pin_code": {
                        "type": "string",
                        "description": "New 4-digit PIN (required for reschedule, keep same for cancel)"
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "New booking time in ISO 8601 (required for reschedule)"
                    },
                    "calendar_event_id": {
                        "type": "string",
                        "description": "Updated calendar event ID (if changed)"
                    }
                },
                "required": ["email", "status"]
            }
        }
    }
]

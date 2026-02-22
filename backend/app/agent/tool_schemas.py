"""
LiteLLM tool schemas for the appointment booking agent.
Tool names match exactly the user's system prompt specification.
"""

TOOL_SCHEMAS = [
    # ── Cal.com tools ─────────────────────────────────────────────────────────

    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": (
                "Check available appointment slots for a given date via Cal.com. "
                "Returns a list of free time slots. ALWAYS call this before creating a booking."
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
                "Create a new appointment booking via Cal.com. "
                "ONLY call this after confirming availability with check_availability. "
                "Returns the booking uid needed for future cancel/reschedule operations."
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
                    "title": {
                        "type": "string",
                        "description": "Meeting title / purpose of the appointment"
                    }
                },
                "required": ["start", "name", "email", "title"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_booking_information",
            "description": (
                "Retrieve existing upcoming bookings for a guest from Cal.com by their email address. "
                "Returns booking details including uid (needed for cancel/reschedule), "
                "date/time, title, and status. ALWAYS call this before cancel/reschedule."
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
                "Cancel an existing booking in Cal.com. "
                "Requires the uid from get_booking_information AND the attendee email. "
                "PIN MUST be verified BEFORE calling this tool. "
                "The uid MUST come from get_booking_information called with the user's email — never from user input."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "uid": {
                        "type": "string",
                        "description": "Cal.com booking uid from get_booking_information (never from user input)"
                    },
                    "attendee_email": {
                        "type": "string",
                        "description": "Email address of the booking owner — used to verify ownership"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for cancellation (optional)"
                    }
                },
                "required": ["uid", "attendee_email"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "reschedule_booking",
            "description": (
                "Reschedule an existing booking to a new time via Cal.com. "
                "Requires the uid from get_booking_information, the attendee email, and the new start time. "
                "PIN MUST be verified BEFORE calling this tool. "
                "The uid MUST come from get_booking_information called with the user's email — never from user input. "
                "A new unique PIN should be generated after successful rescheduling."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "uid": {
                        "type": "string",
                        "description": "Cal.com booking uid from get_booking_information (never from user input)"
                    },
                    "attendee_email": {
                        "type": "string",
                        "description": "Email address of the booking owner — used to verify ownership"
                    },
                    "new_start": {
                        "type": "string",
                        "description": "New start time in ISO 8601 format (e.g., 2026-02-21T14:00:00+04:00)"
                    }
                },
                "required": ["uid", "attendee_email", "new_start"]
            }
        }
    },

    # ── Database / guest record tools ─────────────────────────────────────────

    {
        "type": "function",
        "function": {
            "name": "search_guest",
            "description": (
                "Look up a guest record by email address in the database. "
                "Returns the guest's name, PIN code (for internal verification only — NEVER reveal it), "
                "booking time, and status. "
                "ALWAYS call this before cancel or reschedule to retrieve the stored PIN."
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
            "name": "add_to_list",
            "description": (
                "Add a NEW guest record to the database. "
                "Use ONLY when creating a brand new booking — NOT for cancel/reschedule. "
                "Include the unique 4-digit PIN generated for this guest."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Guest's full name"},
                    "email": {"type": "string", "description": "Guest's email address"},
                    "pin_code": {
                        "type": "string",
                        "description": "Unique 4-digit PIN code (e.g., '4821')"
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "Booking start time in ISO 8601 format"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["Active"],
                        "description": "Record status — always 'Active' for new bookings"
                    },
                    "meeting_title": {
                        "type": "string",
                        "description": "Meeting title / purpose"
                    },
                    "booking_uid": {
                        "type": "string",
                        "description": "Cal.com booking uid returned by create_booking"
                    }
                },
                "required": ["name", "email", "pin_code", "booking_time", "status"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "update_the_list",
            "description": (
                "Update an EXISTING guest record in the database. "
                "Use for cancellations (status='Canceled') and rescheduling (new booking_time + new PIN). "
                "Do NOT use this for new bookings — use add_to_list instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Guest's email address (used to find the record)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["Active", "Canceled", "Rescheduled"],
                        "description": "New status for the record"
                    },
                    "pin_code": {
                        "type": "string",
                        "description": "New 4-digit PIN (required for reschedule; keep existing for cancel)"
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "New booking time in ISO 8601 (required for reschedule)"
                    },
                    "meeting_title": {
                        "type": "string",
                        "description": "Updated meeting title (optional)"
                    },
                    "booking_uid": {
                        "type": "string",
                        "description": "Updated Cal.com booking uid (for reschedule)"
                    }
                },
                "required": ["email", "status"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "search_all_guests",
            "description": (
                "Retrieve all guest records from the database for this instance. "
                "Use this to check existing PIN codes before generating a new one "
                "to ensure uniqueness. Returns a list of {email, pin_code, name, status}."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    # ── Email tool ────────────────────────────────────────────────────────────

    {
        "type": "function",
        "function": {
            "name": "send_booking_email",
            "description": (
                "Send an email notification to the guest after a booking action. "
                "MUST be called after: (1) creating a booking, (2) canceling a booking, "
                "(3) rescheduling a booking. Do NOT call for availability checks."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_name": {"type": "string", "description": "Guest's full name"},
                    "email_address": {"type": "string", "description": "Guest's email address"},
                    "email_content": {
                        "type": "object",
                        "description": "Email subject and body",
                        "properties": {
                            "subject": {"type": "string", "description": "Email subject line"},
                            "body": {"type": "string", "description": "Email body text (plain text or markdown)"}
                        },
                        "required": ["subject", "body"]
                    }
                },
                "required": ["guest_name", "email_address", "email_content"]
            }
        }
    },
]

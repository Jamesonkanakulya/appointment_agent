from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


# Auth
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


# Global Settings
class GlobalSettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    # SMTP
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None


class GlobalSettingsResponse(BaseModel):
    llm_provider: str
    llm_base_url: str
    llm_api_key_set: bool
    llm_model: str
    updated_at: datetime
    # SMTP (password not exposed)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_configured: bool = False

    class Config:
        from_attributes = True


# Instances
class InstanceCreate(BaseModel):
    name: str
    webhook_path: str
    calcom_api_key: Optional[str] = None
    calcom_event_type_id: Optional[int] = None
    timezone: str = "UTC"
    timezone_offset: str = "+00:00"
    business_name: str
    workday_start: str = "09:00"
    workday_end: str = "17:00"
    # Per-instance SMTP
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None


class InstanceUpdate(BaseModel):
    name: Optional[str] = None
    webhook_path: Optional[str] = None
    calcom_api_key: Optional[str] = None
    calcom_event_type_id: Optional[int] = None
    timezone: Optional[str] = None
    timezone_offset: Optional[str] = None
    business_name: Optional[str] = None
    workday_start: Optional[str] = None
    workday_end: Optional[str] = None
    # Per-instance SMTP
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None


class InstanceResponse(BaseModel):
    id: uuid.UUID
    name: str
    webhook_path: str
    calcom_event_type_id: Optional[int] = None
    calcom_api_key_configured: bool
    timezone: str
    timezone_offset: str
    business_name: str
    workday_start: str
    workday_end: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Per-instance SMTP (password not exposed)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_configured: bool = False

    class Config:
        from_attributes = True


# Guest Records
class GuestRecordResponse(BaseModel):
    id: int
    instance_id: uuid.UUID
    name: Optional[str]
    email: str
    pin_code: str
    booking_time: Optional[datetime]
    status: str
    meeting_title: Optional[str]
    calendar_event_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Sessions
class SessionResponse(BaseModel):
    session_id: str
    updated_at: datetime
    message_count: int

    class Config:
        from_attributes = True


# Webhook
class WebhookRequest(BaseModel):
    sessionId: str
    message: str
    metadata: Optional[dict] = None


class WebhookResponse(BaseModel):
    response: str
    sessionId: str

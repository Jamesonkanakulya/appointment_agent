from pydantic import BaseModel, EmailStr
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


class GlobalSettingsResponse(BaseModel):
    llm_provider: str
    llm_base_url: str
    llm_api_key_set: bool  # Don't expose the actual key
    llm_model: str
    updated_at: datetime

    class Config:
        from_attributes = True


# Instances
class InstanceCreate(BaseModel):
    name: str
    webhook_path: str
    calendar_provider: str = "google"

    google_service_account_json: Optional[str] = None
    google_calendar_id: Optional[str] = None

    microsoft_client_id: Optional[str] = None
    microsoft_client_secret: Optional[str] = None
    microsoft_tenant_id: Optional[str] = None
    microsoft_user_email: Optional[str] = None

    timezone: str = "UTC"
    timezone_offset: str = "+00:00"
    business_name: str
    workday_start: str = "09:00"
    workday_end: str = "17:00"


class InstanceUpdate(InstanceCreate):
    name: Optional[str] = None
    webhook_path: Optional[str] = None
    business_name: Optional[str] = None


class InstanceResponse(BaseModel):
    id: uuid.UUID
    name: str
    webhook_path: str
    calendar_provider: str

    google_calendar_id: Optional[str] = None
    google_service_account_configured: bool

    microsoft_client_id: Optional[str] = None
    microsoft_tenant_id: Optional[str] = None
    microsoft_user_email: Optional[str] = None
    microsoft_secret_configured: bool

    timezone: str
    timezone_offset: str
    business_name: str
    workday_start: str
    workday_end: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

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

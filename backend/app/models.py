import uuid
from datetime import datetime
from sqlalchemy import (
    String, Integer, Boolean, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import mapped_column, Mapped, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GlobalSettings(Base):
    __tablename__ = "global_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    llm_provider: Mapped[str] = mapped_column(String(50), default="openai")
    llm_base_url: Mapped[str] = mapped_column(Text, default="https://models.github.ai/inference")
    llm_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # Fernet-encrypted
    llm_model: Mapped[str] = mapped_column(String(100), default="openai/gpt-4o")
    provider_api_keys: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON {provider_id: enc_key}
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # SMTP email settings (optional)
    smtp_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(Text, nullable=True)  # Fernet-encrypted
    smtp_from_email: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Instance(Base):
    __tablename__ = "instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    webhook_path: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Cal.com credentials
    calcom_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)  # Fernet-encrypted
    calcom_event_type_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Per-instance SMTP (overrides Global Settings when configured)
    smtp_host: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(Text, nullable=True)  # Fernet-encrypted
    smtp_from_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Common config
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    timezone_offset: Mapped[str] = mapped_column(String(10), default="+00:00")
    business_name: Mapped[str] = mapped_column(String(100), nullable=False)
    workday_start: Mapped[str] = mapped_column(String(5), default="09:00")
    workday_end: Mapped[str] = mapped_column(String(5), default="17:00")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guests: Mapped[list["GuestRecord"]] = relationship("GuestRecord", back_populates="instance", cascade="all, delete-orphan")
    conversations: Mapped[list["ConversationHistory"]] = relationship("ConversationHistory", back_populates="instance", cascade="all, delete-orphan")


class GuestRecord(Base):
    __tablename__ = "guest_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instances.id", ondelete="CASCADE"))
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    pin_code: Mapped[str] = mapped_column(String(10), nullable=False)
    booking_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Active")
    meeting_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    calendar_event_id: Mapped[str | None] = mapped_column(Text, nullable=True)  # Cal.com booking uid
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instance: Mapped["Instance"] = relationship("Instance", back_populates="guests")


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("instances.id", ondelete="CASCADE"))
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    messages: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instance: Mapped["Instance"] = relationship("Instance", back_populates="conversations")

    __table_args__ = (UniqueConstraint("instance_id", "session_id"),)

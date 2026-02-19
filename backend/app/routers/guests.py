import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..database import get_db
from ..models import GuestRecord, ConversationHistory, Instance, User
from ..auth import get_current_user
from ..schemas import GuestRecordResponse, SessionResponse

router = APIRouter(prefix="/api/instances", tags=["guests"])


@router.get("/{instance_id}/guests", response_model=list[GuestRecordResponse])
async def list_guests(
    instance_id: uuid.UUID,
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    query = select(GuestRecord).where(GuestRecord.instance_id == instance_id)
    if status:
        query = query.where(GuestRecord.status == status)
    query = query.order_by(GuestRecord.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{instance_id}/sessions", response_model=list[SessionResponse])
async def list_sessions(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ConversationHistory)
        .where(ConversationHistory.instance_id == instance_id)
        .order_by(ConversationHistory.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        SessionResponse(
            session_id=s.session_id,
            updated_at=s.updated_at,
            message_count=len(s.messages)
        )
        for s in sessions
    ]


@router.delete("/{instance_id}/sessions/{session_id}", status_code=204)
async def delete_session(
    instance_id: uuid.UUID,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    await db.execute(
        delete(ConversationHistory).where(
            ConversationHistory.instance_id == instance_id,
            ConversationHistory.session_id == session_id
        )
    )
    await db.commit()

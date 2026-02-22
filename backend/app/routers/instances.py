import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Instance, User
from ..auth import get_current_user
from ..encryption import encrypt, decrypt
from ..schemas import InstanceCreate, InstanceUpdate, InstanceResponse

router = APIRouter(prefix="/api/instances", tags=["instances"])


def _to_response(inst: Instance) -> InstanceResponse:
    smtp_configured = bool(inst.smtp_host and inst.smtp_user and inst.smtp_password)
    return InstanceResponse(
        id=inst.id,
        name=inst.name,
        webhook_path=inst.webhook_path,
        calcom_event_type_id=inst.calcom_event_type_id,
        calcom_api_key_configured=bool(inst.calcom_api_key),
        timezone=inst.timezone,
        timezone_offset=inst.timezone_offset,
        business_name=inst.business_name,
        workday_start=inst.workday_start,
        workday_end=inst.workday_end,
        is_active=inst.is_active,
        created_at=inst.created_at,
        updated_at=inst.updated_at,
        smtp_host=inst.smtp_host,
        smtp_port=inst.smtp_port,
        smtp_user=inst.smtp_user,
        smtp_from_email=inst.smtp_from_email,
        smtp_configured=smtp_configured,
    )


@router.get("", response_model=list[InstanceResponse])
async def list_instances(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    result = await db.execute(select(Instance).order_by(Instance.created_at))
    return [_to_response(i) for i in result.scalars().all()]


@router.post("", response_model=InstanceResponse, status_code=201)
async def create_instance(
    body: InstanceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    existing = await db.execute(select(Instance).where(Instance.webhook_path == body.webhook_path))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="webhook_path already in use")

    inst = Instance(
        name=body.name,
        webhook_path=body.webhook_path,
        calcom_api_key=encrypt(body.calcom_api_key) if body.calcom_api_key else None,
        calcom_event_type_id=body.calcom_event_type_id,
        timezone=body.timezone,
        timezone_offset=body.timezone_offset,
        business_name=body.business_name,
        workday_start=body.workday_start,
        workday_end=body.workday_end,
        smtp_host=body.smtp_host,
        smtp_port=body.smtp_port or 587,
        smtp_user=body.smtp_user,
        smtp_password=encrypt(body.smtp_password) if body.smtp_password else None,
        smtp_from_email=body.smtp_from_email,
    )
    db.add(inst)
    await db.commit()
    await db.refresh(inst)
    return _to_response(inst)


@router.get("/{instance_id}", response_model=InstanceResponse)
async def get_instance(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    inst = result.scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    return _to_response(inst)


@router.put("/{instance_id}", response_model=InstanceResponse)
async def update_instance(
    instance_id: uuid.UUID,
    body: InstanceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    inst = result.scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")

    if body.name is not None:
        inst.name = body.name
    if body.webhook_path is not None and body.webhook_path != inst.webhook_path:
        existing = await db.execute(select(Instance).where(Instance.webhook_path == body.webhook_path))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="webhook_path already in use")
        inst.webhook_path = body.webhook_path
    if body.calcom_api_key is not None:
        inst.calcom_api_key = encrypt(body.calcom_api_key) if body.calcom_api_key else None
    if body.calcom_event_type_id is not None:
        inst.calcom_event_type_id = body.calcom_event_type_id
    if body.timezone is not None:
        inst.timezone = body.timezone
    if body.timezone_offset is not None:
        inst.timezone_offset = body.timezone_offset
    if body.business_name is not None:
        inst.business_name = body.business_name
    if body.workday_start is not None:
        inst.workday_start = body.workday_start
    if body.workday_end is not None:
        inst.workday_end = body.workday_end
    if body.smtp_host is not None:
        inst.smtp_host = body.smtp_host or None
    if body.smtp_port is not None:
        inst.smtp_port = body.smtp_port
    if body.smtp_user is not None:
        inst.smtp_user = body.smtp_user or None
    if body.smtp_password is not None:
        inst.smtp_password = encrypt(body.smtp_password) if body.smtp_password else None
    if body.smtp_from_email is not None:
        inst.smtp_from_email = body.smtp_from_email or None

    await db.commit()
    await db.refresh(inst)
    return _to_response(inst)


@router.delete("/{instance_id}", status_code=204)
async def delete_instance(
    instance_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    result = await db.execute(select(Instance).where(Instance.id == instance_id))
    inst = result.scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail="Instance not found")
    await db.delete(inst)
    await db.commit()

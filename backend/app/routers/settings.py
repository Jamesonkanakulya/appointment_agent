from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import GlobalSettings, User
from ..auth import get_current_user
from ..encryption import encrypt, decrypt
from ..schemas import GlobalSettingsUpdate, GlobalSettingsResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=GlobalSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    result = await db.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not initialized")
    return GlobalSettingsResponse(
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        llm_api_key_set=bool(settings.llm_api_key),
        llm_model=settings.llm_model,
        updated_at=settings.updated_at,
    )


@router.put("", response_model=GlobalSettingsResponse)
async def update_settings(
    body: GlobalSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    result = await db.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        settings = GlobalSettings(id=1)
        db.add(settings)

    if body.llm_provider is not None:
        settings.llm_provider = body.llm_provider
    if body.llm_base_url is not None:
        settings.llm_base_url = body.llm_base_url
    if body.llm_api_key is not None:
        settings.llm_api_key = encrypt(body.llm_api_key) if body.llm_api_key else None
    if body.llm_model is not None:
        settings.llm_model = body.llm_model

    await db.commit()
    await db.refresh(settings)
    return GlobalSettingsResponse(
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        llm_api_key_set=bool(settings.llm_api_key),
        llm_model=settings.llm_model,
        updated_at=settings.updated_at,
    )

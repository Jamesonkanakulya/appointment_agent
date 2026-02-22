import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import GlobalSettings, User
from ..auth import get_current_user
from ..encryption import encrypt, decrypt
from ..schemas import GlobalSettingsUpdate, GlobalSettingsResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _load_provider_keys(settings: GlobalSettings) -> dict:
    """Return the {provider_id: encrypted_key} dict stored in provider_api_keys."""
    try:
        return json.loads(settings.provider_api_keys or "{}")
    except Exception:
        return {}


def _derive_provider_id(provider: str, base_url: str | None) -> str:
    """Map (llm_provider, base_url) → a unique frontend provider id."""
    if provider == "openai" and base_url and "github.ai" in base_url:
        return "openai_github"
    return provider


def _to_response(settings: GlobalSettings) -> GlobalSettingsResponse:
    provider_keys = _load_provider_keys(settings)
    provider_keys_set = {k: True for k, v in provider_keys.items() if v}
    return GlobalSettingsResponse(
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        llm_api_key_set=bool(settings.llm_api_key),
        llm_model=settings.llm_model,
        updated_at=settings.updated_at,
        provider_keys_set=provider_keys_set,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_user=settings.smtp_user,
        smtp_from_email=settings.smtp_from_email,
        smtp_configured=bool(settings.smtp_host and settings.smtp_user and settings.smtp_password),
    )


@router.get("", response_model=GlobalSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    result = await db.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
    settings = result.scalar_one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not initialized")
    return _to_response(settings)


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

    provider_keys = _load_provider_keys(settings)

    # Determine which provider id we are saving for
    new_provider_id = body.llm_provider_id  # e.g. "openai_github", "anthropic", "openai"
    if not new_provider_id:
        # Derive from the incoming provider + base_url (or fall back to current)
        incoming_provider = body.llm_provider or settings.llm_provider
        incoming_base_url = body.llm_base_url if body.llm_base_url is not None else settings.llm_base_url
        new_provider_id = _derive_provider_id(incoming_provider, incoming_base_url)

    old_provider_id = _derive_provider_id(settings.llm_provider, settings.llm_base_url)

    if body.llm_api_key is not None:
        # User entered a key (non-None means the field was explicitly sent)
        if body.llm_api_key:
            encrypted = encrypt(body.llm_api_key)
            provider_keys[new_provider_id] = encrypted
            settings.llm_api_key = encrypted
        # If empty string sent, treat as "keep existing" — do nothing
    else:
        # No key submitted — check if switching providers
        if new_provider_id != old_provider_id and new_provider_id in provider_keys:
            # Auto-load the saved key for the newly selected provider
            settings.llm_api_key = provider_keys[new_provider_id]

    settings.provider_api_keys = json.dumps(provider_keys)

    if body.llm_provider is not None:
        settings.llm_provider = body.llm_provider
    if body.llm_base_url is not None:
        settings.llm_base_url = body.llm_base_url
    if body.llm_model is not None:
        settings.llm_model = body.llm_model

    # SMTP settings
    if body.smtp_host is not None:
        settings.smtp_host = body.smtp_host or None
    if body.smtp_port is not None:
        settings.smtp_port = body.smtp_port
    if body.smtp_user is not None:
        settings.smtp_user = body.smtp_user or None
    if body.smtp_password is not None:
        settings.smtp_password = encrypt(body.smtp_password) if body.smtp_password else None
    if body.smtp_from_email is not None:
        settings.smtp_from_email = body.smtp_from_email or None

    await db.commit()
    await db.refresh(settings)
    return _to_response(settings)

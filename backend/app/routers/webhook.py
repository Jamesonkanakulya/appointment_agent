from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Instance
from ..schemas import WebhookRequest, WebhookResponse
from ..agent.runner import run_agent

router = APIRouter(tags=["webhook"])


@router.post("/webhook/{webhook_path}", response_model=WebhookResponse)
async def handle_webhook(
    webhook_path: str,
    body: WebhookRequest,
    db: AsyncSession = Depends(get_db)
):
    # Find the instance for this webhook path
    result = await db.execute(
        select(Instance).where(
            Instance.webhook_path == webhook_path,
            Instance.is_active == True
        )
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=404, detail=f"No active instance found for webhook path: {webhook_path}")

    if not body.sessionId or not body.sessionId.strip():
        raise HTTPException(status_code=400, detail="sessionId is required and must be non-empty")
    if not body.message or not body.message.strip():
        raise HTTPException(status_code=400, detail="message is required and must be non-empty")

    try:
        response_text = await run_agent(
            session_id=body.sessionId.strip(),
            user_message=body.message.strip(),
            instance=instance,
            db=db,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return WebhookResponse(response=response_text, sessionId=body.sessionId)

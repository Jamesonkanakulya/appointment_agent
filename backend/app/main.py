import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import select

from .database import engine, AsyncSessionLocal, Base
from .models import User, GlobalSettings
from .auth import hash_password
from .encryption import encrypt
from .config import settings
from .routers import auth, instances, settings as settings_router, guests, webhook

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed initial data
    async with AsyncSessionLocal() as db:
        # Create first admin user if no users exist
        result = await db.execute(select(User))
        if not result.first():
            user = User(
                username=settings.first_user,
                password_hash=hash_password(settings.first_password),
            )
            db.add(user)
            logger.info(f"Created first admin user: {settings.first_user}")

        # Create default global settings if not exists
        result = await db.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        if not result.scalar_one_or_none():
            api_key = settings.github_token or ""
            gs = GlobalSettings(
                id=1,
                llm_provider="openai",
                llm_base_url="https://models.github.ai/inference",
                llm_api_key=encrypt(api_key) if api_key else None,
                llm_model="openai/gpt-4o",
            )
            db.add(gs)
            logger.info("Created default global LLM settings (GitHub Models / GPT-4o)")

        await db.commit()

    yield

    await engine.dispose()


app = FastAPI(title="Appointment Agent", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router)
app.include_router(instances.router)
app.include_router(settings_router.router)
app.include_router(guests.router)
app.include_router(webhook.router)

# Serve React frontend (if built static files exist)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"message": "Frontend not built. Run: cd frontend && npm run build"}

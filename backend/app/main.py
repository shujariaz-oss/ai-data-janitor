"""FastAPI main application with lifespan events and router registration."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.api import auth, audit, billing, cleaning, crm, webhooks
from app.config import get_settings
from app.db import engine
from app.models import Base
from app.utils import configure_logging, get_logger

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("app_startup")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("app_shutdown")
    await engine.dispose()


app = FastAPI(
    title="AI Data Janitor",
    description="Autonomous CRM data cleaning micro-SaaS",
    version="1.0.0",
    lifespan=lifespan,
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(crm.router, prefix="/crm", tags=["crm"])
app.include_router(cleaning.router, prefix="/cleaning", tags=["cleaning"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])
app.include_router(audit.router, prefix="/audit", tags=["audit"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

"""Webhook router: receives CRM change notifications and verifies signatures."""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_webhook_signature
from app.db import get_db
from app.models import CRMConnection, CRMType, User
from app.api.auth import get_current_user
from app.tasks.cleaning import run_cleaning_pipeline
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/{crm_type}")
async def receive_webhook(request: Request, crm_type: CRMType, x_hubspot_signature: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    stmt = select(CRMConnection).where(CRMConnection.crm_type == crm_type)
    result = await db.execute(stmt)
    connections = result.scalars().all()
    if not connections:
        raise HTTPException(status_code=404, detail="No connection found for CRM type")
    for conn in connections:
        if conn.webhook_secret:
            sig = x_hubspot_signature or request.headers.get("X-Salesforce-Signature", "")
            if not verify_webhook_signature(payload, sig, conn.webhook_secret):
                logger.warning("webhook_signature_invalid", connection_id=str(conn.id))
                continue
        task = run_cleaning_pipeline.delay(str(conn.id), trigger_type="webhook")
        logger.info("webhook_triggered", connection_id=str(conn.id), task_id=task.id)
        return {"status": "queued", "task_id": task.id}
    return {"status": "processed"}


@router.post("/stripe")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"), db: AsyncSession = Depends(get_db)):
    from app.api.billing import stripe_webhook as billing_stripe_webhook
    return await billing_stripe_webhook(request, db)

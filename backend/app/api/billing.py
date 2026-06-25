"""Billing router: usage dashboard and Stripe integration."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_org, get_current_user
from app.config import get_settings
from app.db import get_db
from app.models import Organization, UsageEvent, User
from app.schemas import BillingPortalResponse, UsageSummary
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/usage", response_model=UsageSummary)
async def get_usage(org: Organization = Depends(get_current_org), db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    stmt = select(func.sum(UsageEvent.record_count)).where(UsageEvent.organization_id == org.id, UsageEvent.timestamp >= start_of_month)
    result = await db.execute(stmt)
    total_records = result.scalar() or 0
    cost_cents = total_records * settings.billable_unit_price_cents
    free_used = org.settings.get("free_tier_used", 0)
    free_remaining = max(0, settings.free_records_per_month - free_used)
    return UsageSummary(current_month_records=total_records, current_month_cost_cents=cost_cents, free_remaining=free_remaining, unit_price_cents=settings.billable_unit_price_cents)


@router.post("/checkout")
async def create_checkout(request: Request, org: Organization = Depends(get_current_org), db: AsyncSession = Depends(get_db)):
    if not settings.stripe_secret_key or not settings.stripe_price_id:
        raise HTTPException(status_code=503, detail="Stripe not configured")
    import stripe
    stripe.api_key = settings.stripe_secret_key
    if not org.stripe_customer_id:
        customer = stripe.Customer.create(name=org.name, metadata={"org_id": str(org.id)})
        org.stripe_customer_id = customer.id
        await db.commit()
    session = stripe.checkout.Session.create(customer=org.stripe_customer_id, payment_method_types=["card"], mode="subscription", line_items=[{"price": settings.stripe_price_id, "quantity": 1}], success_url=str(request.url_for("billing_success")), cancel_url=str(request.url_for("billing_cancel")))
    return {"checkout_url": session.url}


@router.post("/portal", response_model=BillingPortalResponse)
async def customer_portal(request: Request, org: Organization = Depends(get_current_org)):
    if not settings.stripe_secret_key or not org.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer")
    import stripe
    stripe.api_key = settings.stripe_secret_key
    session = stripe.billing_portal.Session.create(customer=org.stripe_customer_id, return_url=str(request.url_for("billing_portal")))
    return BillingPortalResponse(url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook secret not configured")
    import stripe
    stripe.api_key = settings.stripe_secret_key
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except Exception as e:
        logger.error("stripe_webhook_invalid", error=str(e))
        raise HTTPException(status_code=400, detail="Invalid signature")
    if event["type"] == "invoice.payment_succeeded":
        org_id = event["data"]["object"].get("customer")
        stmt = select(Organization).where(Organization.stripe_customer_id == org_id)
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()
        if org:
            org.settings["billing_status"] = "active"
            await db.commit()
            logger.info("invoice_payment_succeeded", org_id=str(org.id))
    elif event["type"] == "invoice.payment_failed":
        org_id = event["data"]["object"].get("customer")
        stmt = select(Organization).where(Organization.stripe_customer_id == org_id)
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()
        if org:
            org.settings["billing_status"] = "past_due"
            await db.commit()
            logger.warning("invoice_payment_failed", org_id=str(org.id))
    return {"status": "received"}


@router.get("/success")
async def billing_success():
    return {"message": "Subscription successful! You can now use AI Data Janitor."}


@router.get("/cancel")
async def billing_cancel():
    return {"message": "Subscription cancelled."}


@router.get("/portal")
async def billing_portal():
    return {"message": "Welcome to the billing portal."}

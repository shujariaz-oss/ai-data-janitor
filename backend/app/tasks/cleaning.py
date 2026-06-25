"""Celery tasks for the cleaning pipeline."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from celery import chain, chord, group
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cleaning.deduplication import DeduplicationEngine
from app.cleaning.normalization import normalize_record
from app.config import get_settings
from app.crm.salesforce import SalesforceAdapter
from app.crm.hubspot import HubSpotAdapter
from app.db import AsyncSessionLocal
from app.enrichment.orchestrator import EnrichmentOrchestrator
from app.models import CRMConnection, CRMRecord, CleaningAction, CleaningJob, CRMType, FieldChange, JobStatus, Organization, UsageEvent
from app.utils import get_correlation_id, get_logger
from app.tasks.celery import celery_app

logger = get_logger(__name__)
settings = get_settings()


def get_adapter(connection: CRMConnection):
    decrypted_access = connection.encrypted_access_token
    decrypted_refresh = connection.encrypted_refresh_token
    kwargs = {
        "client_id": settings.salesforce_client_id if connection.crm_type == CRMType.SALESFORCE else settings.hubspot_client_id,
        "client_secret": settings.salesforce_client_secret if connection.crm_type == CRMType.SALESFORCE else settings.hubspot_client_secret,
    }
    if connection.crm_type == CRMType.SALESFORCE:
        return SalesforceAdapter(str(connection.id), decrypted_access, decrypted_refresh, instance_url=kwargs.get("instance_url"), **kwargs)
    else:
        return HubSpotAdapter(str(connection.id), decrypted_access, decrypted_refresh, **kwargs)


@celery_app.task(bind=True, max_retries=3)
def run_cleaning_pipeline(self, connection_id: str, trigger_type: str = "webhook"):
    import asyncio
    asyncio.run(_run_pipeline(str(connection_id), trigger_type, self.request.id))


async def _run_pipeline(connection_id: str, trigger_type: str, task_id: str):
    async with AsyncSessionLocal() as db:
        stmt = select(CRMConnection).where(CRMConnection.id == connection_id)
        result = await db.execute(stmt)
        connection = result.scalar_one_or_none()
        if not connection or connection.status != "active":
            logger.warning("pipeline_connection_inactive", connection_id=connection_id)
            return

        org_stmt = select(Organization).where(Organization.id == connection.organization_id)
        org_result = await db.execute(org_stmt)
        org = org_result.scalar_one()

        job = CleaningJob(organization_id=org.id, status=JobStatus.RUNNING, trigger_type=trigger_type, metadata={"task_id": task_id, "connection_id": str(connection_id)}, started_at=datetime.now(timezone.utc))
        db.add(job)
        await db.commit()
        await db.refresh(job)

        try:
            adapter = get_adapter(connection)
            since = connection.last_sync_at or (datetime.now(timezone.utc) - timedelta(days=1))
            records = []
            async for rec in adapter.fetch_modified_records(since):
                records.append(rec)

            job.record_count = len(records)
            await db.commit()

            normalizer = Normalizer(rules=org.settings.get("normalization_rules", {}))
            normalized_records = []
            for rec in records:
                norm = normalizer.normalize(rec, rec.get("object_type", "Contact"))
                normalized_records.append(norm)

            engine = DeduplicationEngine(threshold=settings.dedup_threshold, auto_merge_threshold=settings.auto_merge_threshold)
            duplicates = engine.find_duplicates(normalized_records)
            auto_merge_pairs = [d for d in duplicates if engine.should_auto_merge(d[2])]

            enrichment = EnrichmentOrchestrator(db, sources=org.settings.get("enrichment_sources", ["cache", "clearbit", "hunter"]))
            enriched_records = []
            for rec in normalized_records:
                missing = _identify_missing_fields(rec)
                if missing:
                    enriched = await enrichment.enrich_record(rec, missing)
                    enriched_records.append(enriched)
                else:
                    enriched_records.append(rec)

            changes_count = 0
            for rec in enriched_records:
                changes = _compute_changes(rec, records)
                if changes:
                    await adapter.update_record(rec["Id"], changes)
                    for field, (old, new) in changes.items():
                        fc = FieldChange(job_id=job.id, record_id=rec["Id"], field_name=field, old_value=old, new_value=new, action=CleaningAction.NORMALIZE)
                        db.add(fc)
                        changes_count += 1

            for master_id, dup_id, conf, details in auto_merge_pairs:
                try:
                    await adapter.merge_records(master_id, [dup_id])
                    fc = FieldChange(job_id=job.id, record_id=master_id, field_name="merge", old_value=dup_id, new_value=master_id, action=CleaningAction.MERGE, confidence=conf)
                    db.add(fc)
                    changes_count += 1
                except Exception as e:
                    logger.error("merge_failed", master_id=master_id, dup_id=dup_id, error=str(e))

            job.processed_count = len(enriched_records)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            connection.last_sync_at = datetime.now(timezone.utc)

            billable_count = max(0, changes_count - org.settings.get("free_tier_used", 0))
            if billable_count > 0:
                cost = billable_count * settings.billable_unit_price_cents
                job.cost_cents = cost
                event = UsageEvent(organization_id=org.id, event_type="clean", record_count=billable_count, unit_price_cents=settings.billable_unit_price_cents)
                db.add(event)
                await _send_usage_to_stripe(org, event, db)

            await db.commit()
            logger.info("pipeline_completed", job_id=str(job.id), records_processed=len(enriched_records), changes=changes_count)

        except Exception as e:
            logger.error("pipeline_failed", job_id=str(job.id), error=str(e))
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
            raise


class Normalizer:
    def __init__(self, rules=None):
        from app.cleaning.normalization import Normalizer as BaseNormalizer
        self.norm = BaseNormalizer(rules=rules)
    def normalize(self, record, object_type):
        return self.norm.normalize(record, object_type)


def _identify_missing_fields(record: dict) -> List[str]:
    missing = []
    for field in ["Email", "Phone", "Title", "Company", "Industry", "LinkedIn"]:
        if not record.get(field):
            missing.append(field)
    return missing


def _compute_changes(final: dict, originals: List[dict]) -> dict:
    original = next((r for r in originals if r.get("Id") == final.get("Id")), {})
    changes = {}
    for key in set(list(original.keys()) + list(final.keys())):
        if key in ("Id", "object_type", "CreatedDate", "LastModifiedDate"):
            continue
        old = original.get(key)
        new = final.get(key)
        if old != new and new is not None:
            changes[key] = (old, new)
    return changes


async def _send_usage_to_stripe(org, event, db):
    if not settings.stripe_secret_key or not org.stripe_subscription_id:
        return
    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key
        sub = stripe.Subscription.retrieve(org.stripe_subscription_id)
        item_id = None
        for item in sub["items"]["data"]:
            if item["price"]["id"] == settings.stripe_price_id:
                item_id = item["id"]
                break
        if item_id:
            usage = stripe.SubscriptionItem.create_usage_record(item_id, quantity=event.record_count, timestamp=int(event.timestamp.timestamp()), idempotency_key=str(event.id))
            event.stripe_usage_record_id = usage.id
            event.sent_to_billing = True
            await db.commit()
            logger.info("stripe_usage_sent", event_id=str(event.id), quantity=event.record_count)
    except Exception as e:
        logger.error("stripe_usage_failed", event_id=str(event.id), error=str(e))


@celery_app.task
def send_usage_to_billing(organization_id: str, record_count: int):
    import asyncio
    asyncio.run(_send_billing_task(organization_id, record_count))


async def _send_billing_task(organization_id: str, record_count: int):
    async with AsyncSessionLocal() as db:
        stmt = select(Organization).where(Organization.id == organization_id)
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()
        if not org:
            return
        event = UsageEvent(organization_id=org.id, event_type="clean", record_count=record_count, unit_price_cents=settings.billable_unit_price_cents)
        db.add(event)
        await db.commit()
        await db.refresh(event)
        await _send_usage_to_stripe(org, event, db)

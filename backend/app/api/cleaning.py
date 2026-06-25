"""Cleaning router: jobs, settings, triggers."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_org, get_current_user
from app.config import get_settings
from app.db import get_db
from app.models import CleaningJob, JobStatus, Organization, User
from app.schemas import CleaningJobOut, CleaningSettings, OrganizationSettingsUpdate
from app.tasks.cleaning import run_cleaning_pipeline
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/jobs", response_model=list[CleaningJobOut])
async def list_jobs(status: Optional[JobStatus] = None, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(CleaningJob).where(CleaningJob.organization_id == user.organization_id)
    if status:
        stmt = stmt.where(CleaningJob.status == status)
    stmt = stmt.order_by(CleaningJob.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/trigger")
async def trigger_cleaning(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    connection_id = data.get("connection_id")
    if not connection_id:
        raise HTTPException(status_code=422, detail="connection_id required")
    from app.models import CRMConnection
    stmt = select(CRMConnection).where(CRMConnection.id == connection_id, CRMConnection.organization_id == user.organization_id)
    result = await db.execute(stmt)
    conn = result.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")

    task = run_cleaning_pipeline.delay(str(conn.id), trigger_type="manual")
    logger.info("cleaning_triggered", connection_id=connection_id, task_id=task.id)
    return {"task_id": task.id, "connection_id": connection_id, "status": "queued"}


@router.get("/settings", response_model=CleaningSettings)
async def get_cleaning_settings(org: Organization = Depends(get_current_org)):
    s = org.settings
    return CleaningSettings(
        normalization_rules=s.get("normalization_rules", {}),
        dedup_auto_merge=s.get("dedup_auto_merge", False),
        enrichment_sources=s.get("enrichment_sources", ["cache", "clearbit", "hunter"]),
        allow_overwrite=s.get("allow_overwrite", False),
    )


@router.put("/settings")
async def update_cleaning_settings(data: CleaningSettings, org: Organization = Depends(get_current_org), db: AsyncSession = Depends(get_db)):
    org.settings.update({
        "normalization_rules": data.normalization_rules,
        "dedup_auto_merge": data.dedup_auto_merge,
        "enrichment_sources": data.enrichment_sources,
        "allow_overwrite": data.allow_overwrite,
    })
    await db.commit()
    return data

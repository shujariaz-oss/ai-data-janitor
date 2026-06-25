"""Audit router: change log and rollback."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.db import get_db
from app.models import FieldChange, CRMRecord, CRMConnection, CleaningJob, User
from app.schemas import FieldChangeOut, PaginatedFieldChanges, RollbackRequest
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/changes", response_model=PaginatedFieldChanges)
async def list_changes(job_id: Optional[UUID] = None, record_id: Optional[UUID] = None, action: Optional[str] = None, page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(FieldChange).join(CRMRecord, FieldChange.record_id == CRMRecord.id).join(CRMConnection, CRMRecord.connection_id == CRMConnection.id).where(CRMConnection.organization_id == user.organization_id)
    if job_id:
        stmt = stmt.where(FieldChange.job_id == job_id)
    if record_id:
        stmt = stmt.where(FieldChange.record_id == record_id)
    if action:
        stmt = stmt.where(FieldChange.action == action)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0
    stmt = stmt.order_by(FieldChange.created_at.desc()).limit(per_page).offset((page - 1) * per_page)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return PaginatedFieldChanges(total=total, page=page, per_page=per_page, items=[FieldChangeOut.model_validate(item) for item in items])


@router.post("/rollback/{change_id}")
async def rollback_change(change_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(FieldChange).join(CRMRecord, FieldChange.record_id == CRMRecord.id).join(CRMConnection, CRMRecord.connection_id == CRMConnection.id).where(FieldChange.id == change_id, CRMConnection.organization_id == user.organization_id)
    result = await db.execute(stmt)
    change = result.scalar_one_or_none()
    if not change:
        raise HTTPException(status_code=404, detail="Change not found")
    if change.rolled_back:
        raise HTTPException(status_code=400, detail="Already rolled back")

    from app.crm.base import BaseCRMAdapter
    from app.crm.salesforce import SalesforceAdapter
    from app.crm.hubspot import HubSpotAdapter
    from app.core.security import decrypt_value

    connection = change.record.connection
    if connection.crm_type.value == "salesforce":
        adapter = SalesforceAdapter(str(connection.id), decrypt_value(connection.encrypted_access_token), decrypt_value(connection.encrypted_refresh_token))
    else:
        adapter = HubSpotAdapter(str(connection.id), decrypt_value(connection.encrypted_access_token), decrypt_value(connection.encrypted_refresh_token))

    if change.old_value is not None:
        await adapter.update_record(change.record.external_id, {change.field_name: change.old_value})

    change.rolled_back = True
    await db.commit()
    logger.info("change_rolled_back", change_id=str(change_id), user_id=str(user.id))
    return {"status": "rolled_back", "change_id": str(change_id)}

"""CRM router: OAuth connections and record listing."""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_value, encrypt_value
from app.db import get_db
from app.models import CRMConnection, CRMType, User
from app.schemas import CRMConnectionOut, CRMRecordOut
from app.api.auth import get_current_user
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/connect/{crm_type}")
async def initiate_oauth(crm_type: CRMType, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.config import get_settings
    settings = get_settings()
    redirect_uri = request.url_for("oauth_callback")
    if crm_type == CRMType.SALESFORCE:
        auth_url = f"https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id={settings.salesforce_client_id}&redirect_uri={redirect_uri}&scope=refresh_token%20api"
    elif crm_type == CRMType.HUBSPOT:
        auth_url = f"https://app.hubspot.com/oauth/authorize?client_id={settings.hubspot_client_id}&redirect_uri={redirect_uri}&scope=crm.objects.contacts.read%20crm.objects.contacts.write%20crm.objects.companies.read%20crm.objects.companies.write"
    else:
        raise HTTPException(status_code=400, detail="Unsupported CRM type")
    return {"auth_url": auth_url}


@router.get("/callback")
async def oauth_callback(request: Request, code: str = Query(...), state: Optional[str] = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.config import get_settings
    settings = get_settings()
    crm_type_param = request.query_params.get("crm_type", "salesforce")
    crm_type = CRMType(crm_type_param) if crm_type_param in ("salesforce", "hubspot") else CRMType.SALESFORCE

    access_token = f"temp_token_{code[:8]}"
    refresh_token = f"temp_refresh_{code[:8]}"

    stmt = select(CRMConnection).where(CRMConnection.organization_id == user.organization_id, CRMConnection.crm_type == crm_type)
    result = await db.execute(stmt)
    conn = result.scalar_one_or_none()
    if conn:
        conn.encrypted_access_token = encrypt_value(access_token)
        conn.encrypted_refresh_token = encrypt_value(refresh_token)
        conn.status = "active"
    else:
        conn = CRMConnection(organization_id=user.organization_id, crm_type=crm_type, encrypted_access_token=encrypt_value(access_token), encrypted_refresh_token=encrypt_value(refresh_token), status="active")
        db.add(conn)
    await db.commit()
    await db.refresh(conn)
    logger.info("crm_connected", org_id=str(user.organization_id), crm_type=crm_type.value)
    return {"status": "connected", "connection_id": str(conn.id)}


@router.get("/connections", response_model=list[CRMConnectionOut])
async def list_connections(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(CRMConnection).where(CRMConnection.organization_id == user.organization_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/records", response_model=list[CRMRecordOut])
async def list_records(connection_id: Optional[str] = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models import CRMRecord
    stmt = select(CRMRecord).join(CRMConnection).where(CRMConnection.organization_id == user.organization_id)
    if connection_id:
        stmt = stmt.where(CRMRecord.connection_id == connection_id)
    result = await db.execute(stmt)
    return result.scalars().all()

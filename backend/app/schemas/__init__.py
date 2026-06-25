"""Pydantic request/response schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    organization_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    stripe_customer_id: Optional[str]
    settings: dict
    created_at: datetime


class OrganizationSettingsUpdate(BaseModel):
    settings: dict


class CRMConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    crm_type: str
    status: str
    last_sync_at: Optional[datetime]
    created_at: datetime


class CRMRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    external_id: str
    object_type: str
    raw_data: dict
    cleaned_data: Optional[dict]
    cleaned_at: Optional[datetime]
    created_at: datetime


class CleaningJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    record_count: int
    processed_count: int
    cost_cents: int
    trigger_type: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class CleaningSettings(BaseModel):
    normalization_rules: dict = Field(default_factory=dict)
    dedup_auto_merge: bool = False
    enrichment_sources: list[str] = Field(default_factory=lambda: ["cache", "clearbit", "hunter"])
    allow_overwrite: bool = False


class FieldChangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    job_id: UUID
    record_id: UUID
    field_name: str
    old_value: Optional[str]
    new_value: Optional[str]
    action: str
    confidence: Optional[float]
    rolled_back: bool
    created_at: datetime


class RollbackRequest(BaseModel):
    change_id: UUID


class UsageSummary(BaseModel):
    current_month_records: int
    current_month_cost_cents: int
    free_remaining: int
    unit_price_cents: int


class BillingPortalResponse(BaseModel):
    url: str


class StripeWebhookEvent(BaseModel):
    pass


class PaginatedFieldChanges(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[FieldChangeOut]

"""Integration tests for billing pipeline."""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Organization, UsageEvent
from app.tasks.cleaning import _send_usage_to_stripe


class TestBilling:
    @pytest.mark.asyncio
    async def test_send_usage_to_stripe_no_config(self, db: AsyncSession):
        org = Organization(name="Test Org")
        db.add(org)
        await db.commit()
        await db.refresh(org)

        event = UsageEvent(organization_id=org.id, record_count=10)
        db.add(event)
        await db.commit()

        await _send_usage_to_stripe(org, event, db)
        assert event.sent_to_billing is False

    @pytest.mark.asyncio
    async def test_usage_event_creation(self, db: AsyncSession):
        org = Organization(name="Test Org")
        db.add(org)
        await db.commit()
        await db.refresh(org)

        event = UsageEvent(organization_id=org.id, event_type="clean", record_count=5, unit_price_cents=2)
        db.add(event)
        await db.commit()

        assert event.record_count == 5
        assert event.unit_price_cents == 2
        assert event.sent_to_billing is False

    @pytest.mark.asyncio
    async def test_billing_cost_calculation(self, db: AsyncSession):
        from app.config import get_settings
        settings = get_settings()
        records = 100
        expected_cost = records * settings.billable_unit_price_cents
        assert expected_cost == 200

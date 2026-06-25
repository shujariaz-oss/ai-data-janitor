"""Integration tests for FastAPI auth endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import User, Organization


@pytest.mark.asyncio
async def test_register_and_login(db: AsyncSession):
    from app.db import get_db
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User",
            "organization_name": "Test Org",
        })
        assert resp.status_code == 200
        token = resp.json()["access_token"]
        assert token

        resp = await client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "securepassword123",
        })
        assert resp.status_code == 200
        assert resp.json()["access_token"]

    app.dependency_overrides.clear()

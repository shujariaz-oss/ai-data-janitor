"""Enrichment orchestrator: fetch missing data from external sources."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models import EnrichmentCache
from app.utils import get_logger, mask_pii_in_dict

logger = get_logger(__name__)
settings = get_settings()


class EnrichmentProvider:
    name: str = "base"
    async def enrich(self, record: dict, missing_fields: List[str]) -> Optional[dict]:
        raise NotImplementedError


class ClearbitProvider(EnrichmentProvider):
    name = "clearbit"
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def enrich(self, record: dict, missing_fields: List[str]) -> Optional[dict]:
        email = record.get("Email") or record.get("email")
        domain = record.get("Domain") or record.get("domain")
        if not email and not domain:
            return None
        if not settings.clearbit_api_key:
            return None
        async with httpx.AsyncClient(timeout=10) as client:
            if email:
                url = f"https://person.clearbit.com/v2/combined/find?email={email}"
            else:
                url = f"https://company.clearbit.com/v2/companies/find?domain={domain}"
            headers = {"Authorization": f"Bearer {settings.clearbit_api_key}"}
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            logger.info("clearbit_no_result", status=resp.status_code, email=email, domain=domain)
        return None


class HunterProvider(EnrichmentProvider):
    name = "hunter"
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def enrich(self, record: dict, missing_fields: List[str]) -> Optional[dict]:
        domain = record.get("Domain") or record.get("domain") or record.get("Company")
        if not domain or not settings.hunter_api_key:
            return None
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={settings.hunter_api_key}"
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return {"hunter": data}
            logger.info("hunter_no_result", status=resp.status_code, domain=domain)
        return None


class EnrichmentOrchestrator:
    def __init__(self, db: AsyncSession, sources: Optional[List[str]] = None):
        self.db = db
        self.sources = sources or ["clearbit", "hunter"]
        self.providers: Dict[str, EnrichmentProvider] = {}
        if "clearbit" in self.sources:
            self.providers["clearbit"] = ClearbitProvider()
        if "hunter" in self.sources:
            self.providers["hunter"] = HunterProvider()

    async def enrich_record(self, record: dict, missing_fields: List[str]) -> dict:
        result = dict(record)
        filled = {}
        for source_name in self.sources:
            provider = self.providers.get(source_name)
            if not provider:
                continue
            cache_key = self._cache_key(record, source_name)
            cached = await self._get_cache(cache_key)
            if cached:
                logger.info("cache_hit", source=source_name, cache_key=cache_key)
                data = cached
            else:
                try:
                    data = await provider.enrich(record, missing_fields)
                except Exception as e:
                    logger.error("enrichment_error", source=source_name, error=str(e))
                    data = None
                if data:
                    await self._set_cache(cache_key, data)
            if data:
                filled = self._apply_data(result, data, missing_fields)
                result.update(filled)
                if all(result.get(f) for f in missing_fields):
                    break
        return result

    async def _get_cache(self, query_hash: str) -> Optional[dict]:
        stmt = select(EnrichmentCache).where(EnrichmentCache.query_hash == query_hash, EnrichmentCache.expires_at > datetime.now(timezone.utc))
        result = await self.db.execute(stmt)
        row = result.scalar_one_or_none()
        return row.response if row else None

    async def _set_cache(self, query_hash: str, data: dict):
        cache = EnrichmentCache(query_hash=query_hash, source="auto", response=data, expires_at=datetime.now(timezone.utc) + timedelta(hours=24))
        self.db.add(cache)
        await self.db.commit()

    @staticmethod
    def _cache_key(record: dict, source: str) -> str:
        email = record.get("Email") or record.get("email")
        domain = record.get("Domain") or record.get("domain")
        key = f"{source}:{email}:{domain}"
        return hashlib.sha256(key.encode()).hexdigest()[:32]

    @staticmethod
    def _apply_data(record: dict, data: dict, missing_fields: List[str]) -> dict:
        filled = {}
        person = data.get("person")
        if person:
            if "LinkedIn" in missing_fields or "linkedin_url" in missing_fields:
                linkedin = person.get("linkedin")
                if linkedin:
                    filled["LinkedIn"] = linkedin
            if "Title" in missing_fields or "title" in missing_fields:
                title = person.get("employment", {}).get("title")
                if title:
                    filled["Title"] = title
            if "Company" in missing_fields or "company" in missing_fields:
                company = person.get("employment", {}).get("name")
                if company:
                    filled["Company"] = company
        company = data.get("company")
        if company:
            if "Industry" in missing_fields or "industry" in missing_fields:
                industry = company.get("category", {}).get("industry")
                if industry:
                    filled["Industry"] = industry
            if "Domain" in missing_fields or "domain" in missing_fields:
                domain = company.get("domain")
                if domain:
                    filled["Domain"] = domain
        hunter = data.get("hunter", {}).get("data")
        if hunter:
            emails = hunter.get("emails", [])
            if emails and ("Email" in missing_fields or "email" in missing_fields):
                filled["Email"] = emails[0].get("value")
        return filled

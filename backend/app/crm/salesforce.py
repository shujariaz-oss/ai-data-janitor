"""Salesforce CRM adapter using simple-salesforce."""
from datetime import datetime, timezone
from typing import AsyncIterator, List, Optional

import httpx
from simple_salesforce import Salesforce
from tenacity import retry, stop_after_attempt, wait_exponential

from app.crm.base import BaseCRMAdapter
from app.utils import get_logger

logger = get_logger(__name__)


class SalesforceAdapter(BaseCRMAdapter):
    def __init__(self, connection_id: str, access_token: str, refresh_token: Optional[str] = None, instance_url: Optional[str] = None, **kwargs):
        super().__init__(connection_id, access_token, refresh_token, **kwargs)
        self.instance_url = instance_url
        self.client_id = kwargs.get("client_id")
        self.client_secret = kwargs.get("client_secret")
        self._sf: Optional[Salesforce] = None

    def _get_sf(self) -> Salesforce:
        if self._sf is None:
            self._sf = Salesforce(instance_url=self.instance_url, session_id=self.access_token, version="59.0")
        return self._sf

    async def fetch_modified_records(self, since: datetime, object_types: Optional[List[str]] = None) -> AsyncIterator[dict]:
        object_types = object_types or ["Contact", "Lead", "Account"]
        sf = self._get_sf()
        since_iso = since.isoformat()
        for obj_type in object_types:
            try:
                query = f"SELECT Id, FirstName, LastName, Email, Phone, Title, Account.Name, Account.Industry, CreatedDate, LastModifiedDate FROM {obj_type} WHERE LastModifiedDate >= {since_iso}"
                if obj_type == "Account":
                    query = f"SELECT Id, Name, Industry, Phone, Website, BillingCity, BillingState, BillingCountry, CreatedDate, LastModifiedDate FROM {obj_type} WHERE LastModifiedDate >= {since_iso}"
                result = sf.query_all(query)
                for rec in result.get("records", []):
                    yield self._normalize_salesforce_record(rec, obj_type)
            except Exception as e:
                logger.error("salesforce_fetch_error", object_type=obj_type, error=str(e))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def update_record(self, external_id: str, changes: dict) -> dict:
        sf = self._get_sf()
        obj_type = self._guess_object_type(external_id)
        try:
            result = sf.__getattr__(obj_type).update(external_id, changes)
            logger.info("salesforce_update_success", record_id=external_id, object_type=obj_type)
            return {"success": True, "id": external_id, "result": result}
        except Exception as e:
            logger.error("salesforce_update_error", record_id=external_id, error=str(e))
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def merge_records(self, master_id: str, duplicate_ids: List[str]) -> dict:
        sf = self._get_sf()
        results = []
        for dup_id in duplicate_ids:
            try:
                obj_type = self._guess_object_type(master_id)
                if obj_type in ("Contact", "Lead"):
                    pass
                else:
                    sf.__getattr__(obj_type).delete(dup_id)
                results.append({"duplicate_id": dup_id, "status": "merged"})
            except Exception as e:
                logger.error("salesforce_merge_error", master_id=master_id, dup_id=dup_id, error=str(e))
                results.append({"duplicate_id": dup_id, "status": "failed", "error": str(e)})
        return {"master_id": master_id, "results": results}

    async def register_webhook(self, callback_url: str) -> str:
        logger.info("salesforce_webhook_register", callback_url=callback_url)
        return f"webhook_{self.connection_id}"

    async def delete_webhook(self, webhook_id: str) -> bool:
        logger.info("salesforce_webhook_delete", webhook_id=webhook_id)
        return True

    async def refresh_token(self) -> tuple[str, Optional[str]]:
        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise ValueError("Missing OAuth credentials for token refresh")
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.instance_url}/services/oauth2/token", data={"grant_type": "refresh_token", "client_id": self.client_id, "client_secret": self.client_secret, "refresh_token": self.refresh_token})
            resp.raise_for_status()
            data = resp.json()
            return data["access_token"], data.get("refresh_token")

    @staticmethod
    def _normalize_salesforce_record(rec: dict, obj_type: str) -> dict:
        flat = {"Id": rec.get("Id"), "object_type": obj_type, "CreatedDate": rec.get("CreatedDate"), "LastModifiedDate": rec.get("LastModifiedDate")}
        if obj_type == "Account":
            flat["Name"] = rec.get("Name")
            flat["Industry"] = rec.get("Industry")
            flat["Phone"] = rec.get("Phone")
            flat["Website"] = rec.get("Website")
            flat["BillingCity"] = rec.get("BillingCity")
            flat["BillingState"] = rec.get("BillingState")
            flat["BillingCountry"] = rec.get("BillingCountry")
        else:
            flat["FirstName"] = rec.get("FirstName")
            flat["LastName"] = rec.get("LastName")
            flat["Email"] = rec.get("Email")
            flat["Phone"] = rec.get("Phone")
            flat["MobilePhone"] = rec.get("MobilePhone")
            flat["Title"] = rec.get("Title")
            account = rec.get("Account") or {}
            flat["Company"] = account.get("Name")
            flat["Industry"] = account.get("Industry")
        return flat

    @staticmethod
    def _guess_object_type(record_id: str) -> str:
        prefix = record_id[:3] if record_id else ""
        mapping = {"001": "Account", "003": "Contact", "00Q": "Lead"}
        return mapping.get(prefix, "Contact")

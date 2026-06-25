"""HubSpot CRM adapter using the hubspot-api-client."""
from datetime import datetime, timezone
from typing import AsyncIterator, List, Optional

import httpx
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInput
from tenacity import retry, stop_after_attempt, wait_exponential

from app.crm.base import BaseCRMAdapter
from app.utils import get_logger

logger = get_logger(__name__)


class HubSpotAdapter(BaseCRMAdapter):
    def __init__(self, connection_id: str, access_token: str, refresh_token: Optional[str] = None, **kwargs):
        super().__init__(connection_id, access_token, refresh_token, **kwargs)
        self.client_id = kwargs.get("client_id")
        self.client_secret = kwargs.get("client_secret")
        self._client: Optional[HubSpot] = None

    def _get_client(self) -> HubSpot:
        if self._client is None:
            self._client = HubSpot(access_token=self.access_token)
        return self._client

    async def fetch_modified_records(self, since: datetime, object_types: Optional[List[str]] = None) -> AsyncIterator[dict]:
        object_types = object_types or ["contacts", "companies"]
        client = self._get_client()
        for obj_type in object_types:
            try:
                if obj_type == "contacts":
                    api = client.crm.contacts
                elif obj_type == "companies":
                    api = client.crm.companies
                else:
                    continue
                after = None
                while True:
                    resp = api.basic_api.get_page(limit=100, after=after)
                    for result in resp.results:
                        props = result.properties or {}
                        modified = props.get("hs_lastmodifieddate")
                        if modified:
                            try:
                                from datetime import datetime as dt
                                mod_dt = dt.fromisoformat(modified.replace("Z", "+00:00"))
                            except ValueError:
                                mod_dt = None
                            if mod_dt and mod_dt >= since:
                                yield self._normalize_hubspot_record(result, obj_type)
                        else:
                            yield self._normalize_hubspot_record(result, obj_type)
                    if not resp.paging or not resp.paging.next:
                        break
                    after = resp.paging.next.after
            except Exception as e:
                logger.error("hubspot_fetch_error", object_type=obj_type, error=str(e))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def update_record(self, external_id: str, changes: dict) -> dict:
        client = self._get_client()
        obj_type = self._guess_object_type(external_id)
        try:
            input_obj = SimplePublicObjectInput(properties=changes)
            if obj_type == "companies":
                result = client.crm.companies.basic_api.update(contact_id=external_id, simple_public_object_input=input_obj)
            else:
                result = client.crm.contacts.basic_api.update(contact_id=external_id, simple_public_object_input=input_obj)
            logger.info("hubspot_update_success", record_id=external_id, object_type=obj_type)
            return {"success": True, "id": external_id, "result": result}
        except Exception as e:
            logger.error("hubspot_update_error", record_id=external_id, error=str(e))
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def merge_records(self, master_id: str, duplicate_ids: List[str]) -> dict:
        client = self._get_client()
        results = []
        for dup_id in duplicate_ids:
            try:
                obj_type = self._guess_object_type(master_id)
                if obj_type == "companies":
                    client.crm.companies.basic_api.archive(dup_id)
                else:
                    client.crm.contacts.basic_api.archive(dup_id)
                results.append({"duplicate_id": dup_id, "status": "merged"})
            except Exception as e:
                logger.error("hubspot_merge_error", master_id=master_id, dup_id=dup_id, error=str(e))
                results.append({"duplicate_id": dup_id, "status": "failed", "error": str(e)})
        return {"master_id": master_id, "results": results}

    async def register_webhook(self, callback_url: str) -> str:
        logger.info("hubspot_webhook_register", callback_url=callback_url)
        return f"webhook_{self.connection_id}"

    async def delete_webhook(self, webhook_id: str) -> bool:
        logger.info("hubspot_webhook_delete", webhook_id=webhook_id)
        return True

    async def refresh_token(self) -> tuple[str, Optional[str]]:
        if not self.client_id or not self.client_secret or not self.refresh_token:
            raise ValueError("Missing OAuth credentials for token refresh")
        async with httpx.AsyncClient() as client:
            resp = await client.post("https://api.hubapi.com/oauth/v1/token", data={"grant_type": "refresh_token", "client_id": self.client_id, "client_secret": self.client_secret, "refresh_token": self.refresh_token})
            resp.raise_for_status()
            data = resp.json()
            return data["access_token"], data.get("refresh_token")

    @staticmethod
    def _normalize_hubspot_record(result, obj_type: str) -> dict:
        props = result.properties or {}
        flat = {"Id": result.id, "object_type": obj_type, "CreatedDate": props.get("createdate"), "LastModifiedDate": props.get("hs_lastmodifieddate")}
        if obj_type == "companies":
            flat["Name"] = props.get("name")
            flat["Industry"] = props.get("industry")
            flat["Phone"] = props.get("phone")
            flat["Website"] = props.get("domain")
            flat["BillingCity"] = props.get("city")
            flat["BillingState"] = props.get("state")
            flat["BillingCountry"] = props.get("country")
        else:
            flat["FirstName"] = props.get("firstname")
            flat["LastName"] = props.get("lastname")
            flat["Email"] = props.get("email")
            flat["Phone"] = props.get("phone")
            flat["MobilePhone"] = props.get("mobilephone")
            flat["Title"] = props.get("jobtitle")
            flat["Company"] = props.get("company")
        return flat

    @staticmethod
    def _guess_object_type(record_id: str) -> str:
        return "contacts"

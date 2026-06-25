"""Abstract CRM adapter contract and base utilities."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

from app.utils import get_logger

logger = get_logger(__name__)


class BaseCRMAdapter(ABC):
    def __init__(self, connection_id: str, access_token: str, refresh_token: Optional[str] = None, **kwargs):
        self.connection_id = connection_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.extra = kwargs

    @abstractmethod
    async def fetch_modified_records(self, since: datetime, object_types: Optional[List[str]] = None) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    async def update_record(self, external_id: str, changes: dict) -> dict:
        ...

    @abstractmethod
    async def merge_records(self, master_id: str, duplicate_ids: List[str]) -> dict:
        ...

    @abstractmethod
    async def register_webhook(self, callback_url: str) -> str:
        ...

    @abstractmethod
    async def delete_webhook(self, webhook_id: str) -> bool:
        ...

    @abstractmethod
    async def refresh_token(self) -> tuple[str, Optional[str]]:
        ...

    async def maybe_refresh(self, expires_at: Optional[datetime]) -> str:
        from datetime import timezone
        if expires_at and datetime.now(timezone.utc) >= expires_at:
            new_token, new_refresh = await self.refresh_token()
            self.access_token = new_token
            if new_refresh:
                self.refresh_token = new_refresh
            return new_token
        return self.access_token

"""Shared utilities: logging, correlation IDs, pagination helpers."""
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


def get_correlation_id() -> str:
    cid = correlation_id_var.get()
    if not cid:
        cid = str(uuid.uuid4())[:8]
        correlation_id_var.set(cid)
    return cid


def mask_pii_in_dict(data: dict) -> dict:
    pii_keys = {"email", "phone", "phone_number", "mobile", "address", "street"}
    masked = {}
    for k, v in data.items():
        if k.lower() in pii_keys and isinstance(v, str):
            masked[k] = v[:2] + "****" if len(v) > 4 else "****"
        else:
            masked[k] = v
    return masked

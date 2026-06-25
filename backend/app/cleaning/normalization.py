"""Field normalisation utilities for CRM records."""
import re
from typing import Any, Optional

import phonenumbers
from titlecase import titlecase

from app.config import get_settings
from app.utils import get_logger

logger = get_logger(__name__)
settings = get_settings()

DEFAULT_TITLE_RULES = {
    "vp": "Vice President", "svp": "Senior Vice President", "evp": "Executive Vice President",
    "cfo": "Chief Financial Officer", "ceo": "Chief Executive Officer", "cto": "Chief Technology Officer",
    "cmo": "Chief Marketing Officer", "coo": "Chief Operating Officer", "cio": "Chief Information Officer",
    "cco": "Chief Commercial Officer", "chro": "Chief Human Resources Officer", "md": "Managing Director",
    "gm": "General Manager", "pm": "Product Manager", "ae": "Account Executive",
    "sdr": "Sales Development Representative", "bdr": "Business Development Representative",
    "se": "Solutions Engineer", "swe": "Software Engineer", "eng": "Engineer", "dev": "Developer",
    "qa": "Quality Assurance", "ux": "User Experience", "ui": "User Interface", "hr": "Human Resources",
    "it": "Information Technology", "ops": "Operations", "bizdev": "Business Development",
    "custsuccess": "Customer Success", "cs": "Customer Success",
}

COMPANY_SUFFIXES = [
    (r"\bInc\.?\b", "Inc."), (r"\bLLC\b", "LLC"), (r"\bLtd\.?\b", "Ltd."),
    (r"\bCorp\.?\b", "Corp."), (r"\bCorporation\b", "Corp."), (r"\bLimited\b", "Ltd."),
    (r"\bGmbH\b", "GmbH"), (r"\bAG\b", "AG"), (r"\bBV\b", "BV"),
    (r"\bS\.A\.\b", "S.A."), (r"\bPty\b", "Pty"), (r"\bPLC\b", "PLC"),
]


class Normalizer:
    def __init__(self, rules: Optional[dict] = None):
        self.rules = rules or {}
        self.title_rules = {**DEFAULT_TITLE_RULES, **self.rules.get("titles", {})}

    def normalize(self, record: dict, object_type: str) -> dict:
        result = dict(record)
        result = self._normalize_company_name(result)
        result = self._normalize_person_name(result)
        result = self._normalize_title(result)
        result = self._normalize_phone(result)
        result = self._normalize_email(result)
        result = self._normalize_address(result)
        result = self._normalize_industry(result)
        return result

    def _normalize_company_name(self, record: dict) -> dict:
        name = record.get("Company") or record.get("AccountName") or record.get("company")
        if not name or not isinstance(name, str):
            return record
        name = name.strip()
        name = titlecase(name)
        for pattern, replacement in COMPANY_SUFFIXES:
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)
        name = " ".join(name.split())
        key = "Company" if "Company" in record else ("AccountName" if "AccountName" in record else "company")
        record[key] = name
        return record

    def _normalize_person_name(self, record: dict) -> dict:
        first = record.get("FirstName") or record.get("first_name")
        last = record.get("LastName") or record.get("last_name")
        if first and isinstance(first, str):
            record["FirstName" if "FirstName" in record else "first_name"] = first.strip().title()
        if last and isinstance(last, str):
            record["LastName" if "LastName" in record else "last_name"] = last.strip().title()
        return record

    def _normalize_title(self, record: dict) -> dict:
        title = record.get("Title") or record.get("title") or record.get("JobTitle")
        if not title or not isinstance(title, str):
            return record
        key = "Title" if "Title" in record else ("title" if "title" in record else "JobTitle")
        lower = title.lower().strip()
        for abbr, full in self.title_rules.items():
            if lower == abbr or lower.startswith(abbr + " "):
                title = titlecase(full + title[len(abbr):])
                break
        record[key] = titlecase(title)
        return record

    def _normalize_phone(self, record: dict) -> dict:
        for key in ["Phone", "MobilePhone", "phone", "mobile", "PhoneNumber"]:
            value = record.get(key)
            if value and isinstance(value, str):
                parsed = self._to_e164(value)
                if parsed:
                    record[key] = parsed
        return record

    @staticmethod
    def _to_e164(phone: str, default_region: str = "US") -> Optional[str]:
        try:
            parsed = phonenumbers.parse(phone, default_region)
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            pass
        return None

    def _normalize_email(self, record: dict) -> dict:
        for key in ["Email", "email", "EmailAddress"]:
            value = record.get(key)
            if value and isinstance(value, str):
                record[key] = value.strip().lower()
        return record

    def _normalize_address(self, record: dict) -> dict:
        for key in ["Street", "City", "State", "Country"]:
            value = record.get(key)
            if value and isinstance(value, str):
                record[key] = value.strip().title()
        return record

    def _normalize_industry(self, record: dict) -> dict:
        industry = record.get("Industry") or record.get("industry")
        if industry and isinstance(industry, str):
            record["Industry" if "Industry" in record else "industry"] = industry.strip().title()
        return record


def normalize_record(record: dict, object_type: str, rules: Optional[dict] = None) -> dict:
    return Normalizer(rules=rules).normalize(record, object_type)

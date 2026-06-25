"""Deduplication engine using fuzzy matching and blocking."""
import hashlib
import itertools
from typing import Any, Dict, List, Optional, Tuple

from app.utils import get_logger

logger = get_logger(__name__)


class DeduplicationEngine:
    def __init__(self, threshold: float = 0.85, auto_merge_threshold: float = 0.95):
        self.threshold = threshold
        self.auto_merge_threshold = auto_merge_threshold

    def find_duplicates(self, records: List[Dict[str, Any]], key_fields: Optional[List[str]] = None) -> List[Tuple[str, str, float, Dict[str, Any]]]:
        if not records or len(records) < 2:
            return []
        key_fields = key_fields or ["Email", "Phone", "Company", "FirstName", "LastName"]
        pairs = self._generate_candidate_pairs(records, key_fields)
        results = []
        for rec_a, rec_b in pairs:
            score, details = self._score_pair(rec_a, rec_b, key_fields)
            if score >= self.threshold:
                rid_a = rec_a.get("Id") or rec_a.get("id") or rec_a.get("external_id")
                rid_b = rec_b.get("Id") or rec_b.get("id") or rec_b.get("external_id")
                results.append((rid_a, rid_b, score, details))
        return results

    def _generate_candidate_pairs(self, records: List[Dict[str, Any]], key_fields: List[str]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        blocks: Dict[str, List[Dict[str, Any]]] = {}
        for rec in records:
            keys = self._blocking_keys(rec, key_fields)
            for k in keys:
                blocks.setdefault(k, []).append(rec)
        seen = set()
        pairs = []
        for group in blocks.values():
            if len(group) < 2:
                continue
            for a, b in itertools.combinations(group, 2):
                pair_key = tuple(sorted([str(id(a)), str(id(b))]))
                if pair_key in seen:
                    continue
                seen.add(pair_key)
                pairs.append((a, b))
        return pairs

    def _blocking_keys(self, record: Dict[str, Any], key_fields: List[str]) -> List[str]:
        keys = []
        email = record.get("Email") or record.get("email")
        if email and isinstance(email, str):
            domain = email.split("@")[-1].lower().strip()
            if domain:
                keys.append(f"email_domain:{domain}")
        phone = record.get("Phone") or record.get("phone") or record.get("MobilePhone")
        if phone and isinstance(phone, str):
            digits = "".join(ch for ch in phone if ch.isdigit())
            if len(digits) >= 7:
                keys.append(f"phone:{digits[-7:]}")
        company = record.get("Company") or record.get("company") or record.get("AccountName")
        if company and isinstance(company, str):
            prefix = company.strip().lower()[:6]
            if len(prefix) >= 3:
                keys.append(f"company_prefix:{prefix}")
        first = record.get("FirstName") or record.get("first_name")
        last = record.get("LastName") or record.get("last_name")
        if first and last and isinstance(first, str) and isinstance(last, str):
            keys.append(f"name:{first.strip().lower()[:3]}:{last.strip().lower()[:3]}")
        return keys

    def _score_pair(self, a: Dict[str, Any], b: Dict[str, Any], key_fields: List[str]) -> Tuple[float, Dict[str, Any]]:
        weights = {"Email": 0.35, "Phone": 0.25, "Company": 0.15, "FirstName": 0.125, "LastName": 0.125}
        total_weight = 0.0
        score = 0.0
        details = {}
        for field in key_fields:
            val_a = a.get(field) or a.get(field.lower()) or a.get(field.title())
            val_b = b.get(field) or b.get(field.lower()) or b.get(field.title())
            if not val_a or not val_b or not isinstance(val_a, str) or not isinstance(val_b, str):
                continue
            w = weights.get(field, 0.1)
            total_weight += w
            sim = self._field_similarity(val_a, val_b)
            score += sim * w
            details[field] = round(sim, 3)
        if total_weight == 0:
            return 0.0, {}
        normalized = score / total_weight
        return round(normalized, 4), details

    @staticmethod
    def _field_similarity(a: str, b: str) -> float:
        if a == b:
            return 1.0
        a_norm = a.strip().lower()
        b_norm = b.strip().lower()
        if a_norm == b_norm:
            return 0.98
        def bigrams(s):
            return {s[i:i+2] for i in range(len(s)-1)}
        ba = bigrams(a_norm)
        bb = bigrams(b_norm)
        if not ba or not bb:
            return 0.0
        intersection = len(ba & bb)
        union = len(ba | bb)
        return intersection / union if union else 0.0

    def should_auto_merge(self, confidence: float) -> bool:
        return confidence >= self.auto_merge_threshold


def deduplicate_records(records, threshold=0.85, auto_merge_threshold=0.95):
    engine = DeduplicationEngine(threshold=threshold, auto_merge_threshold=auto_merge_threshold)
    return engine.find_duplicates(records)

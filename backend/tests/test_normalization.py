"""Unit tests for data cleaning normalisation."""
import pytest

from app.cleaning.normalization import Normalizer, normalize_record


class TestNormalization:
    def test_company_name_title_case(self):
        rec = {"Company": "acme corporation INC"}
        result = normalize_record(rec, "Contact")
        assert result["Company"] == "Acme Corporation Inc."

    def test_phone_e164(self):
        rec = {"Phone": "+1 (415) 555-2671"}
        result = normalize_record(rec, "Contact")
        assert result["Phone"] == "+14155552671"

    def test_email_lowercase(self):
        rec = {"Email": "John.Doe@EXAMPLE.COM"}
        result = normalize_record(rec, "Contact")
        assert result["Email"] == "john.doe@example.com"

    def test_title_canonicalization(self):
        rec = {"Title": "vp of sales"}
        result = normalize_record(rec, "Contact")
        assert "Vice President" in result["Title"]

    def test_person_name_title_case(self):
        rec = {"FirstName": "john", "LastName": "doe"}
        result = normalize_record(rec, "Contact")
        assert result["FirstName"] == "John"
        assert result["LastName"] == "Doe"

    def test_custom_rules(self):
        rules = {"titles": {"pm": "Product Manager"}}
        rec = {"Title": "pm"}
        result = Normalizer(rules=rules).normalize(rec, "Contact")
        assert result["Title"] == "Product Manager"

    def test_no_change_when_already_clean(self):
        rec = {"Company": "Acme Inc.", "Phone": "+14155552671", "Email": "john@example.com"}
        result = normalize_record(rec, "Contact")
        assert result["Company"] == "Acme Inc."
        assert result["Phone"] == "+14155552671"
        assert result["Email"] == "john@example.com"

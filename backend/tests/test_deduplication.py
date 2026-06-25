"""Unit tests for deduplication engine."""
import pytest

from app.cleaning.deduplication import DeduplicationEngine, deduplicate_records


class TestDeduplication:
    def test_exact_match(self):
        records = [
            {"Id": "1", "Email": "alice@example.com", "FirstName": "Alice", "LastName": "Smith"},
            {"Id": "2", "Email": "alice@example.com", "FirstName": "Alice", "LastName": "Smith"},
        ]
        engine = DeduplicationEngine(threshold=0.85, auto_merge_threshold=0.95)
        dups = engine.find_duplicates(records)
        assert len(dups) == 1
        assert dups[0][2] >= 0.95

    def test_no_duplicates(self):
        records = [
            {"Id": "1", "Email": "alice@example.com", "FirstName": "Alice", "LastName": "Smith"},
            {"Id": "2", "Email": "bob@example.com", "FirstName": "Bob", "LastName": "Jones"},
        ]
        engine = DeduplicationEngine(threshold=0.85)
        dups = engine.find_duplicates(records)
        assert len(dups) == 0

    def test_fuzzy_match_same_company(self):
        records = [
            {"Id": "1", "Email": "a@acme.com", "FirstName": "Alice", "LastName": "Smith", "Company": "Acme Inc."},
            {"Id": "2", "Email": "a@acme.com", "FirstName": "Alice", "LastName": "Smith", "Company": "Acme Corp."},
        ]
        engine = DeduplicationEngine(threshold=0.85)
        dups = engine.find_duplicates(records)
        assert len(dups) == 1

    def test_auto_merge_threshold(self):
        engine = DeduplicationEngine(auto_merge_threshold=0.95)
        assert engine.should_auto_merge(0.96) is True
        assert engine.should_auto_merge(0.90) is False

    def test_wrapper_function(self):
        records = [
            {"Id": "1", "Email": "alice@example.com"},
            {"Id": "2", "Email": "alice@example.com"},
        ]
        dups = deduplicate_records(records, threshold=0.85)
        assert len(dups) == 1

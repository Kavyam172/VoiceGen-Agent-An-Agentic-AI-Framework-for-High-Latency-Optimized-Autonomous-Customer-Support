"""
test_tools.py — Unit tests for the three LangChain tools.

These tests verify that each tool:
  - Returns valid JSON
  - Contains the expected top-level keys
  - Handles default and custom arguments

No LLM calls are made here; the tools are purely deterministic
(or pseudo-random with seeded values) and safe to test without mocks.

Run with:
    pytest tests/test_tools.py -v
"""

import json
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.tools.dummy_crm_tool import crm_lookup
from app.tools.internet_diagnostic_tool import internet_diagnostic
from app.tools.faq_tool import faq_lookup


# ── CRM Tool Tests ────────────────────────────────────────────────────────────

class TestCRMTool:
    def test_returns_valid_json(self):
        result = crm_lookup.invoke({"customer_id": "C001"})
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_top_level_keys(self):
        result = crm_lookup.invoke({"customer_id": "C001"})
        data = json.loads(result)
        assert "status" in data
        assert "customer" in data
        assert data["status"] == "success"

    def test_known_customer(self):
        result = crm_lookup.invoke({"customer_id": "C001"})
        data = json.loads(result)
        customer = data["customer"]
        assert customer["customer_id"] == "C001"
        assert customer["name"] == "Ravi Sharma"

    def test_unknown_customer_returns_default(self):
        result = crm_lookup.invoke({"customer_id": "ZZZZ"})
        data = json.loads(result)
        assert data["status"] == "success"
        assert "customer" in data

    def test_customer_has_required_fields(self):
        result = crm_lookup.invoke({"customer_id": "C002"})
        data = json.loads(result)
        customer = data["customer"]
        for field in ["name", "plan", "balance", "account_status", "recent_payments"]:
            assert field in customer, f"Missing field: {field}"


# ── Internet Diagnostic Tool Tests ────────────────────────────────────────────

class TestInternetDiagnosticTool:
    def test_returns_valid_json(self):
        result = internet_diagnostic.invoke({"area_code": "110001"})
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_top_level_keys(self):
        result = internet_diagnostic.invoke({"area_code": "110001"})
        data = json.loads(result)
        assert "status" in data
        assert "diagnostic" in data
        assert data["status"] == "success"

    def test_diagnostic_has_recommendation(self):
        result = internet_diagnostic.invoke({"area_code": "110001"})
        data = json.loads(result)
        assert "recommendation" in data["diagnostic"]
        assert len(data["diagnostic"]["recommendation"]) > 0

    def test_area_code_preserved(self):
        result = internet_diagnostic.invoke({"area_code": "400001"})
        data = json.loads(result)
        assert data["area_code"] == "400001"


# ── FAQ Tool Tests ────────────────────────────────────────────────────────────

class TestFAQTool:
    def test_returns_valid_json(self):
        result = faq_lookup.invoke({"query": "how do I reset my password"})
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_top_level_keys(self):
        result = faq_lookup.invoke({"query": "recharge"})
        data = json.loads(result)
        assert "status" in data
        assert "faq" in data
        assert data["status"] == "success"

    def test_faq_has_answer(self):
        result = faq_lookup.invoke({"query": "how to reset password"})
        data = json.loads(result)
        assert "answer" in data["faq"]
        assert len(data["faq"]["answer"]) > 10

    def test_keyword_match_recharge(self):
        result = faq_lookup.invoke({"query": "how do I recharge my account"})
        data = json.loads(result)
        assert data["matched_score"] > 0

    def test_no_match_returns_fallback(self):
        result = faq_lookup.invoke({"query": "xyzzy completely random nonsense query"})
        data = json.loads(result)
        # Should still return a valid response (fallback)
        assert "faq" in data
        assert "answer" in data["faq"]

    def test_plans_query(self):
        result = faq_lookup.invoke({"query": "what plans do you offer"})
        data = json.loads(result)
        assert data["matched_score"] > 0

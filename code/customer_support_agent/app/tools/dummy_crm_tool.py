"""
dummy_crm_tool.py — Simulated CRM (Customer Relationship Management) tool.

In a real system this would make authenticated API calls to Salesforce,
SAP, or a custom CRM platform.  Here we return deterministic fake data
so the assistant can demonstrate personalised responses without needing
live backend infrastructure.

The tool is decorated with @tool so LangChain can discover, describe,
and invoke it as part of an agent's tool belt.
"""

import json
import random
from datetime import datetime, timedelta

from langchain_core.tools import tool

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Fake customer database ────────────────────────────────────────────────────
_FAKE_CUSTOMERS = {
    "C001": {
        "customer_id": "C001",
        "name": "Ravi Sharma",
        "plan": "Unlimited Pro 5G",
        "balance": 245.50,
        "currency": "INR",
        "data_used_gb": 18.3,
        "data_limit_gb": 100.0,
        "last_recharge_date": "2026-05-01",
        "next_renewal_date": "2026-06-01",
        "account_status": "Active",
        "outstanding_dues": 0.0,
        "recent_payments": [
            {"date": "2026-05-01", "amount": 999, "status": "Success"},
            {"date": "2026-04-01", "amount": 999, "status": "Success"},
        ],
    },
    "C002": {
        "customer_id": "C002",
        "name": "Priya Nair",
        "plan": "Basic 4G",
        "balance": 50.00,
        "currency": "INR",
        "data_used_gb": 4.1,
        "data_limit_gb": 10.0,
        "last_recharge_date": "2026-04-25",
        "next_renewal_date": "2026-05-25",
        "account_status": "Active",
        "outstanding_dues": 149.0,
        "recent_payments": [
            {"date": "2026-04-25", "amount": 299, "status": "Success"},
            {"date": "2026-03-25", "amount": 299, "status": "Failed"},
        ],
    },
}

_DEFAULT_CUSTOMER = {
    "customer_id": "C000",
    "name": "Valued Customer",
    "plan": "Standard Plan",
    "balance": 120.00,
    "currency": "INR",
    "data_used_gb": 6.5,
    "data_limit_gb": 20.0,
    "last_recharge_date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
    "next_renewal_date": (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d"),
    "account_status": "Active",
    "outstanding_dues": 0.0,
    "recent_payments": [
        {"date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"), "amount": 499, "status": "Success"},
    ],
}


@tool
def crm_lookup(customer_id: str = "C001") -> str:
    """
    Look up a customer's account details from the CRM system.

    Returns account balance, current plan, data usage, payment history,
    and renewal information for the given customer_id.

    Parameters
    ----------
    customer_id : str
        The unique CRM identifier for the customer (e.g. 'C001').
        Defaults to 'C001' for demo purposes.
    """
    logger.info("CRM lookup called for customer_id=%s", customer_id)

    customer = _FAKE_CUSTOMERS.get(customer_id.upper(), _DEFAULT_CUSTOMER)

    result = {
        "status": "success",
        "customer": customer,
        "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    logger.debug("CRM result: %s", json.dumps(result, indent=2))
    return json.dumps(result, indent=2)

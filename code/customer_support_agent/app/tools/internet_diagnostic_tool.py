"""
internet_diagnostic_tool.py — Simulated network/internet diagnostics tool.

In a production environment this would call NOC (Network Operations Centre)
APIs, ping servers, or query a monitoring platform like Zabbix or Datadog.
Here we return mock diagnostic data with random variation to make the
demo feel realistic.

The tool is decorated with @tool for LangChain discovery and invocation.
"""

import json
import random
from datetime import datetime

from langchain_core.tools import tool

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Simulated diagnostic scenarios ───────────────────────────────────────────
_DIAGNOSTIC_SCENARIOS = [
    {
        "scenario": "all_clear",
        "network_status": "Operational",
        "latency_ms": random.randint(10, 40),
        "packet_loss_pct": 0,
        "signal_strength": "Excellent (-65 dBm)",
        "download_speed_mbps": round(random.uniform(80, 150), 1),
        "upload_speed_mbps": round(random.uniform(20, 50), 1),
        "dns_resolution": "OK",
        "outage_reported": False,
        "recommendation": "Your connection appears healthy. Try restarting your device if issues persist.",
    },
    {
        "scenario": "high_latency",
        "network_status": "Degraded",
        "latency_ms": random.randint(180, 350),
        "packet_loss_pct": round(random.uniform(2, 8), 1),
        "signal_strength": "Fair (-85 dBm)",
        "download_speed_mbps": round(random.uniform(5, 20), 1),
        "upload_speed_mbps": round(random.uniform(1, 5), 1),
        "dns_resolution": "OK",
        "outage_reported": False,
        "recommendation": (
            "High latency detected on your line. This may be caused by network congestion. "
            "We recommend restarting your router and checking for background downloads."
        ),
    },
    {
        "scenario": "outage",
        "network_status": "Outage Detected",
        "latency_ms": None,
        "packet_loss_pct": 100,
        "signal_strength": "No Signal",
        "download_speed_mbps": 0,
        "upload_speed_mbps": 0,
        "dns_resolution": "Failed",
        "outage_reported": True,
        "outage_eta": "2 hours",
        "recommendation": (
            "We have detected a service outage in your area. "
            "Our engineers are working to resolve it. "
            "Estimated restoration time: 2 hours."
        ),
    },
]


@tool
def internet_diagnostic(area_code: str = "110001") -> str:
    """
    Run a simulated internet/network diagnostic for the given area code.

    Checks network status, latency, packet loss, and signal strength.
    Returns a structured diagnostic report with recommendations.

    Parameters
    ----------
    area_code : str
        The customer's postal/area code used to check for local outages.
        Defaults to '110001' (New Delhi) for demo purposes.
    """
    logger.info("Internet diagnostic called for area_code=%s", area_code)

    # In a real system this would be determined by actual network data.
    # For the demo we randomly pick a scenario, weighted towards all_clear.
    scenario = random.choices(
        _DIAGNOSTIC_SCENARIOS,
        weights=[0.60, 0.25, 0.15],
        k=1,
    )[0]

    # Refresh any values that contain random calls so each invocation differs
    result = {
        "status": "success",
        "area_code": area_code,
        "diagnostic": {
            **scenario,
            "latency_ms": random.randint(10, 40) if scenario["scenario"] == "all_clear"
            else scenario["latency_ms"],
            "download_speed_mbps": round(random.uniform(80, 150), 1) if scenario["scenario"] == "all_clear"
            else scenario["download_speed_mbps"],
        },
        "checked_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    logger.debug("Diagnostic result scenario: %s", scenario["scenario"])
    return json.dumps(result, indent=2)

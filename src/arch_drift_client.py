"""ArchDrift client for fetching architecture drift data."""

import os
import requests
from typing import Optional, Dict, Any
from src.logging_layer import log_event, log_error

ARCH_DRIFT_BASE_URL = os.getenv("ARCH_DRIFT_BASE_URL", "http://localhost:9000")
ARCH_DRIFT_ENDPOINT = os.getenv("ARCH_DRIFT_ENDPOINT", "/drifts")  # Can be overridden if endpoint path differs


def fetch_last_arch_drifts(repo: str, limit: int = 5) -> Optional[Dict[str, Any]]:
    """
    Call ArchDrift FastAPI to fetch last N drifts for a repo.
    Returns JSON dict on success, or None on failure.
    """
    try:
        url = f"{ARCH_DRIFT_BASE_URL}{ARCH_DRIFT_ENDPOINT}"
        resp = requests.get(
            url,
            params={"repo": repo, "limit": limit},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        log_error("ARCH_DRIFT", f"Error calling ArchDrift API: {e!r}")
        return None


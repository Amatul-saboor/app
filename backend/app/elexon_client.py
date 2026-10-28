"""Thin client for the two Elexon BMRS datasets used by the dashboard.

Only the /stream endpoints are used: the plain /datasets/WINDFOR endpoint returns
just the most recent forecast, whereas the stream filtered by publish time returns
every historical forecast run, which the decision-time selection depends on.
"""

import json
import urllib.parse
import urllib.request
from datetime import date, datetime

from .config import ELEXON_BASE_URL

TIMEOUT_SECONDS = 60


def _get(path: str, params: dict) -> list[dict]:
    url = f"{ELEXON_BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        payload = json.load(response)
    # Stream endpoints return a bare list; non-stream endpoints wrap it in {"data": [...]}.
    return payload["data"] if isinstance(payload, dict) else payload


def _iso_z(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_wind_forecasts(published_from: datetime, published_to: datetime) -> list[dict]:
    """All WINDFOR forecast values published in [published_from, published_to] (UTC)."""
    return _get(
        "/datasets/WINDFOR/stream",
        {"publishDateTimeFrom": _iso_z(published_from), "publishDateTimeTo": _iso_z(published_to)},
    )


def fetch_wind_actuals(settlement_from: date, settlement_to: date) -> list[dict]:
    """Half-hourly FUELHH outturn for WIND between two settlement dates (inclusive)."""
    return _get(
        "/datasets/FUELHH/stream",
        {
            "settlementDateFrom": settlement_from.isoformat(),
            "settlementDateTo": settlement_to.isoformat(),
            "fuelType": "WIND",
        },
    )

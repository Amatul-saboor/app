"""Loads the pre-fetched Elexon snapshot and indexes it for fast lookups."""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from .config import DATA_FILE


@dataclass(frozen=True)
class DataStore:
    # delivery hour (UTC) -> [(publish_time, forecast MW), ...] sorted by publish time
    forecasts: dict[datetime, list[tuple[datetime, float]]]
    # half-hour start (UTC) -> actual MW
    actuals: dict[datetime, float]
    fetched_at: str
    sources: dict[str, str]

    @property
    def publish_times(self) -> list[datetime]:
        return sorted({publish for runs in self.forecasts.values() for publish, _ in runs})


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def build_store(raw: dict) -> DataStore:
    forecasts: dict[datetime, list[tuple[datetime, float]]] = {}
    for publish, start, value in raw["forecasts"]:
        forecasts.setdefault(_parse(start), []).append((_parse(publish), float(value)))
    for runs in forecasts.values():
        runs.sort()
    actuals = {_parse(start): float(value) for start, value in raw["actuals"]}
    return DataStore(forecasts, actuals, raw.get("fetchedAt", ""), raw.get("sources", {}))


@lru_cache(maxsize=1)
def get_store(path: Path = DATA_FILE) -> DataStore:
    return build_store(json.loads(path.read_text()))

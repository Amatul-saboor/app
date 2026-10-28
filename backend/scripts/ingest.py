"""Download the Elexon data needed for January 2026 purchase decisions into one JSON file.

Run from the backend/ directory:  python -m scripts.ingest

January's data is historical and fixed, so it is fetched once and committed. The API
then serves it from memory instead of calling Elexon on every request.
"""

import json
from datetime import datetime, time, timedelta, timezone

from app.config import DATA_FILE, FIRST_DECISION_DATE, LAST_DECISION_DATE, UK_TZ
from app.elexon_client import fetch_wind_actuals, fetch_wind_forecasts
from app.selection import delivery_window_utc


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def to_iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    delivery_start, _ = delivery_window_utc(FIRST_DECISION_DATE)
    _, delivery_end = delivery_window_utc(LAST_DECISION_DATE)

    # Any forecast usable by a January decision was published between the day before the
    # first decision and the end of the last decision day, whatever cutoff is chosen.
    published_from = datetime.combine(FIRST_DECISION_DATE - timedelta(days=1), time(0), tzinfo=UK_TZ)
    published_to = datetime.combine(LAST_DECISION_DATE + timedelta(days=1), time(0), tzinfo=UK_TZ)

    print(f"Fetching WINDFOR published {published_from:%Y-%m-%d} to {published_to:%Y-%m-%d} ...")
    forecasts: dict[tuple[str, str], float] = {}
    for row in fetch_wind_forecasts(published_from.astimezone(timezone.utc), published_to.astimezone(timezone.utc)):
        start = parse_utc(row["startTime"])
        if delivery_start <= start < delivery_end:
            forecasts[(to_iso(parse_utc(row["publishTime"])), to_iso(start))] = row["generation"]

    delivery_days = (FIRST_DECISION_DATE + timedelta(days=1), LAST_DECISION_DATE + timedelta(days=1))
    print(f"Fetching FUELHH WIND for settlement dates {delivery_days[0]} to {delivery_days[1]} ...")
    # Outturn can be republished; keep the latest publication of each half-hour.
    latest_actuals: dict[str, tuple[str, float]] = {}
    for row in fetch_wind_actuals(*delivery_days):
        if row.get("fuelType") != "WIND":
            continue
        start = parse_utc(row["startTime"])
        if not delivery_start <= start < delivery_end:
            continue
        key, published = to_iso(start), to_iso(parse_utc(row["publishTime"]))
        if key not in latest_actuals or published > latest_actuals[key][0]:
            latest_actuals[key] = (published, row["generation"])

    output = {
        "fetchedAt": to_iso(datetime.now(timezone.utc)),
        "sources": {
            "forecasts": "https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream",
            "actuals": "https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream",
        },
        "forecasts": sorted([publish, start, value] for (publish, start), value in forecasts.items()),
        "actuals": sorted([start, value] for start, (_, value) in latest_actuals.items()),
    }
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(output, separators=(",", ":")))
    publish_runs = len({publish for publish, _ in forecasts})
    print(f"Saved {len(forecasts)} forecast values from {publish_runs} runs and "
          f"{len(latest_actuals)} half-hourly actuals to {DATA_FILE}")


if __name__ == "__main__":
    main()

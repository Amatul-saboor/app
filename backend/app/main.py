"""HTTP API for the wind forecast dashboard."""

from datetime import date, datetime, time
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .analysis import day_view, decision_dates, month_view
from .config import DEFAULT_CUTOFF, FIRST_DECISION_DATE, LAST_DECISION_DATE
from .data_store import get_store

app = FastAPI(title="Wind Forecast Accuracy API")
# The deployed frontend is same-origin; CORS only matters for the Vite dev server.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET"])

CUTOFF_QUERY = Query(DEFAULT_CUTOFF.strftime("%H:%M"), pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
                     description="Decision cutoff, UK local time (HH:MM)")


def parse_cutoff(value: str) -> time:
    return datetime.strptime(value, "%H:%M").time()


@lru_cache(maxsize=32)
def cached_month(cutoff: time) -> dict:
    return month_view(get_store(), cutoff)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/meta")
def meta() -> dict:
    store = get_store()
    return {
        "decisionDates": decision_dates(),
        "defaultCutoff": DEFAULT_CUTOFF.strftime("%H:%M"),
        "dataFetchedAt": store.fetched_at,
        "sources": store.sources,
        "publishRuns": len(store.publish_times),
    }


@app.get("/api/day")
def day(decision_date: date = Query(..., alias="date"), cutoff: str = CUTOFF_QUERY) -> dict:
    if not FIRST_DECISION_DATE <= decision_date <= LAST_DECISION_DATE:
        raise HTTPException(404, f"Decision dates must be between {FIRST_DECISION_DATE} and {LAST_DECISION_DATE}")
    parsed_cutoff = parse_cutoff(cutoff)
    view = day_view(get_store(), decision_date, parsed_cutoff)
    # January-wide error spread at this cutoff, used to draw an uncertainty band on the day chart.
    overall = cached_month(parsed_cutoff)["overall"]
    view["monthErrorBand"] = {"p10": overall["p10"], "p90": overall["p90"]}
    return view


@app.get("/api/summary")
def summary(cutoff: str = CUTOFF_QUERY) -> dict:
    return cached_month(parse_cutoff(cutoff))

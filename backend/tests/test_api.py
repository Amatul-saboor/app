import pytest
from fastapi.testclient import TestClient

from app import main
from app.data_store import build_store

RAW = {
    "fetchedAt": "2026-02-02T00:00:00Z",
    "sources": {},
    "forecasts": [
        ["2026-01-14T07:30:00Z", "2026-01-15T10:00:00Z", 8000],
        ["2026-01-14T09:30:00Z", "2026-01-15T10:00:00Z", 7800],  # after the 09:20 cutoff
    ],
    "actuals": [["2026-01-15T10:00:00Z", 7000], ["2026-01-15T10:30:00Z", 7400]],
}


@pytest.fixture
def client(monkeypatch):
    store = build_store(RAW)
    monkeypatch.setattr(main, "get_store", lambda: store)
    main.cached_month.cache_clear()
    yield TestClient(main.app)
    main.cached_month.cache_clear()


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_day_uses_forecast_available_at_default_cutoff(client):
    body = client.get("/api/day", params={"date": "2026-01-14"}).json()
    ten_am = next(h for h in body["hours"] if h["localHour"] == "10:00")

    assert body["deliveryDate"] == "2026-01-15"
    assert ten_am["forecast"] == 8000
    assert ten_am["actual"] == 7200
    assert ten_am["error"] == 800
    assert body["metrics"]["n"] == 1


def test_later_cutoff_switches_to_newer_forecast(client):
    body = client.get("/api/day", params={"date": "2026-01-14", "cutoff": "10:00"}).json()
    ten_am = next(h for h in body["hours"] if h["localHour"] == "10:00")
    assert ten_am["forecast"] == 7800


def test_rejects_dates_outside_january_decisions(client):
    assert client.get("/api/day", params={"date": "2026-02-01"}).status_code == 404


def test_rejects_malformed_cutoff(client):
    assert client.get("/api/summary", params={"cutoff": "9am"}).status_code == 422


def test_summary_reports_coverage(client):
    body = client.get("/api/summary").json()
    assert body["coverage"]["hours"] == 31 * 24
    assert body["overall"]["n"] == 1

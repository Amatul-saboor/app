"""Turns selected hours into the daily and monthly views served by the API."""

from datetime import date, time, timedelta

from .config import FIRST_DECISION_DATE, LAST_DECISION_DATE, UK_TZ
from .data_store import DataStore
from .metrics import summarize
from .selection import HourResult, delivery_window_utc, select_day


def decision_dates() -> list[date]:
    days = (LAST_DECISION_DATE - FIRST_DECISION_DATE).days + 1
    return [FIRST_DECISION_DATE + timedelta(days=i) for i in range(days)]


def complete_pairs(hours: list[HourResult]) -> list[tuple[float, float]]:
    return [(h.forecast, h.actual) for h in hours if h.error is not None]


def all_hours(store: DataStore, cutoff: time) -> list[HourResult]:
    return [h for d in decision_dates() for h in select_day(store.forecasts, store.actuals, d, cutoff)]


def day_view(store: DataStore, decision_date: date, cutoff: time) -> dict:
    hours = select_day(store.forecasts, store.actuals, decision_date, cutoff)
    start, end = delivery_window_utc(decision_date)
    half_hours = []
    moment = start
    while moment < end:
        half_hours.append({"time": moment, "actual": store.actuals.get(moment)})
        moment += timedelta(minutes=30)

    return {
        "decisionDate": decision_date,
        "deliveryDate": decision_date + timedelta(days=1),
        "cutoff": cutoff.strftime("%H:%M"),
        "publishTimesUsed": sorted({h.publish_time for h in hours if h.publish_time}),
        "hours": [
            {
                "time": h.start,
                "localHour": h.start.astimezone(UK_TZ).strftime("%H:%M"),
                "forecast": h.forecast,
                "actual": h.actual,
                "error": h.error,
                "publishTime": h.publish_time,
                "horizonHours": h.horizon_hours,
            }
            for h in hours
        ],
        "halfHourlyActuals": half_hours,
        "metrics": summarize(complete_pairs(hours)),
    }


def month_view(store: DataStore, cutoff: time) -> dict:
    every_hour = all_hours(store, cutoff)
    return {
        "cutoff": cutoff.strftime("%H:%M"),
        "overall": summarize(complete_pairs(every_hour)),
        "coverage": {
            "hours": len(every_hour),
            "missingForecast": sum(h.forecast is None for h in every_hour),
            "missingActual": sum(h.actual is None for h in every_hour),
        },
    }

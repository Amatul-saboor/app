"""Decision-time forecast selection: the core business rule of the dashboard.

For a purchase decision made on day D at cutoff time T (UK local), every hour of
delivery day D+1 is assigned the most recently published forecast whose publishTime
is strictly before the cutoff. Forecasts published later did not exist when the
buyer committed, so they must never be used to judge that decision.
"""

from bisect import bisect_left
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

from .config import UK_TZ

HALF_HOUR = timedelta(minutes=30)
HOUR = timedelta(hours=1)


@dataclass(frozen=True)
class HourResult:
    start: datetime  # UTC start of the delivery hour
    forecast: float | None
    publish_time: datetime | None
    actual: float | None  # mean of the two half-hourly outturns in the hour
    actual_halves: tuple[float | None, float | None]

    @property
    def error(self) -> float | None:
        """Forecast minus actual: positive means wind was over-forecast (shortfall risk)."""
        if self.forecast is None or self.actual is None:
            return None
        return self.forecast - self.actual

    @property
    def horizon_hours(self) -> float | None:
        if self.publish_time is None:
            return None
        return (self.start - self.publish_time).total_seconds() / 3600


def cutoff_utc(decision_date: date, cutoff: time) -> datetime:
    return datetime.combine(decision_date, cutoff, tzinfo=UK_TZ).astimezone(timezone.utc)


def delivery_window_utc(decision_date: date) -> tuple[datetime, datetime]:
    """UTC bounds of the UK delivery day after the decision (23/24/25 hours long)."""
    delivery_day = decision_date + timedelta(days=1)
    start = datetime.combine(delivery_day, time(0), tzinfo=UK_TZ)
    end = datetime.combine(delivery_day + timedelta(days=1), time(0), tzinfo=UK_TZ)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def latest_before(runs: list[tuple[datetime, float]], cutoff: datetime) -> tuple[datetime, float] | None:
    """Latest (publish_time, value) published strictly before cutoff; runs must be sorted by time."""
    index = bisect_left(runs, (cutoff,))
    return runs[index - 1] if index > 0 else None


def hourly_actual(actuals: dict[datetime, float], hour_start: datetime) -> tuple[float | None, tuple]:
    """Average the two half-hourly outturns; None unless both halves are present."""
    halves = (actuals.get(hour_start), actuals.get(hour_start + HALF_HOUR))
    if None in halves:
        return None, halves
    return (halves[0] + halves[1]) / 2, halves


def select_day(
    forecasts: dict[datetime, list[tuple[datetime, float]]],
    actuals: dict[datetime, float],
    decision_date: date,
    cutoff: time,
) -> list[HourResult]:
    """Pair the decision-time forecast with the outturn for every hour of the delivery day."""
    decided_at = cutoff_utc(decision_date, cutoff)
    start, end = delivery_window_utc(decision_date)
    results = []
    hour = start
    while hour < end:
        chosen = latest_before(forecasts.get(hour, []), decided_at)
        actual, halves = hourly_actual(actuals, hour)
        results.append(
            HourResult(
                start=hour,
                forecast=chosen[1] if chosen else None,
                publish_time=chosen[0] if chosen else None,
                actual=actual,
                actual_halves=halves,
            )
        )
        hour += HOUR
    return results

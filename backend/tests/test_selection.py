from datetime import date, datetime, time, timezone

from app.selection import cutoff_utc, delivery_window_utc, hourly_actual, latest_before, select_day


def utc(day: int, hour: int, minute: int = 0, month: int = 1) -> datetime:
    return datetime(2026, month, day, hour, minute, tzinfo=timezone.utc)


RUNS = [(utc(13, 22, 30), 9000.0), (utc(14, 4, 30), 8500.0), (utc(14, 7, 30), 8000.0), (utc(14, 9, 30), 7800.0)]


def test_picks_latest_run_published_before_cutoff():
    assert latest_before(RUNS, utc(14, 9, 20)) == (utc(14, 7, 30), 8000.0)


def test_run_published_exactly_at_cutoff_is_excluded():
    assert latest_before(RUNS, utc(14, 9, 30)) == (utc(14, 7, 30), 8000.0)


def test_no_run_before_cutoff_returns_none():
    assert latest_before(RUNS, utc(13, 22, 0)) is None


def test_cutoff_is_interpreted_in_uk_time():
    assert cutoff_utc(date(2026, 1, 14), time(9, 20)) == utc(14, 9, 20)  # GMT in winter
    assert cutoff_utc(date(2026, 6, 14), time(9, 20)) == utc(14, 8, 20, month=6)  # BST in summer


def test_delivery_window_is_the_next_uk_day():
    assert delivery_window_utc(date(2026, 1, 31)) == (utc(1, 0, month=2), utc(2, 0, month=2))


def test_delivery_window_on_clock_change_day_has_23_hours():
    start, end = delivery_window_utc(date(2026, 3, 28))
    assert (end - start).total_seconds() == 23 * 3600


def test_hourly_actual_requires_both_half_hours():
    actuals = {utc(15, 10): 7000.0, utc(15, 10, 30): 7400.0, utc(15, 11): 6000.0}
    assert hourly_actual(actuals, utc(15, 10))[0] == 7200.0
    assert hourly_actual(actuals, utc(15, 11))[0] is None


def test_select_day_falls_back_per_hour_and_computes_error():
    forecasts = {
        # 00:00 has the 07:30 run; 01:00 only has an older run; later hours have nothing.
        utc(15, 0): [(utc(14, 4, 30), 9500.0), (utc(14, 7, 30), 9000.0), (utc(14, 11, 30), 1.0)],
        utc(15, 1): [(utc(14, 4, 30), 8800.0)],
    }
    actuals = {utc(15, 0): 8000.0, utc(15, 0, 30): 8400.0}

    hours = select_day(forecasts, actuals, date(2026, 1, 14), time(9, 20))

    assert len(hours) == 24
    first, second = hours[0], hours[1]
    assert (first.forecast, first.publish_time, first.actual, first.error) == (9000.0, utc(14, 7, 30), 8200.0, 800.0)
    assert first.horizon_hours == 16.5
    assert (second.forecast, second.publish_time, second.error) == (8800.0, utc(14, 4, 30), None)
    assert hours[2].forecast is None

"""Forecast accuracy statistics. All errors use the convention forecast - actual."""

import math
from statistics import quantiles


def percentile(values: list[float], pct: int) -> float | None:
    """Linear-interpolated percentile (same as numpy's default method)."""
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return quantiles(values, n=100, method="inclusive")[pct - 1]


def summarize(pairs: list[tuple[float, float]]) -> dict:
    """Accuracy summary for (forecast, actual) pairs; incomplete pairs must be filtered out first.

    MAPE is deliberately not reported: dividing by near-zero wind output on calm
    hours makes it explode, so nMAE (MAE relative to mean output) is used instead.
    """
    n = len(pairs)
    if n == 0:
        return {"n": 0, "mae": None, "rmse": None, "bias": None, "nmae": None,
                "maxAbsError": None, "p10": None, "p50": None, "p90": None, "overForecastShare": None}

    errors = [forecast - actual for forecast, actual in pairs]
    mean_actual = sum(actual for _, actual in pairs) / n
    mae = sum(abs(e) for e in errors) / n
    return {
        "n": n,
        "mae": mae,
        "rmse": math.sqrt(sum(e * e for e in errors) / n),
        "bias": sum(errors) / n,
        "nmae": mae / mean_actual if mean_actual > 0 else None,
        "maxAbsError": max(abs(e) for e in errors),
        # P90 of forecast - actual: in 90% of hours, wind fell short of the forecast by at most this much.
        "p10": percentile(errors, 10),
        "p50": percentile(errors, 50),
        "p90": percentile(errors, 90),
        "overForecastShare": sum(e > 0 for e in errors) / n,
    }

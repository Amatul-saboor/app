import math

import pytest

from app.metrics import percentile, summarize


def test_hand_calculated_example():
    # errors: +300, -200, +100
    result = summarize([(3500, 3200), (3800, 4000), (4000, 3900)])

    assert result["n"] == 3
    assert result["mae"] == pytest.approx(200)
    assert result["bias"] == pytest.approx(200 / 3)
    assert result["rmse"] == pytest.approx(math.sqrt((300**2 + 200**2 + 100**2) / 3))
    assert result["maxAbsError"] == 300
    assert result["nmae"] == pytest.approx(200 / ((3200 + 4000 + 3900) / 3))
    assert result["overForecastShare"] == pytest.approx(2 / 3)
    assert result["p50"] == 100


def test_empty_input_returns_nulls_not_zeros():
    result = summarize([])
    assert result["n"] == 0
    assert result["mae"] is None and result["bias"] is None


def test_percentile_matches_linear_interpolation():
    values = [float(v) for v in range(11)]  # 0..10
    assert percentile(values, 10) == pytest.approx(1.0)
    assert percentile(values, 90) == pytest.approx(9.0)
    assert percentile([5.0], 90) == 5.0
    assert percentile([], 90) is None

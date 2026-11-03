import pytest

from app.modules.measurements import metrics


def m(day, hour=12, **over):
    base = {"ts": f"2026-10-{day:02d}T{hour:02d}:00:00Z", "weight_kg": 70, "alert": False}
    return {**base, **over}


def points(values):
    return [(metrics.parse_ts(f"2026-10-{d:02d}T00:00:00Z"), v) for d, v in values]


def test_slope_of_consecutive_days_is_minus_one_per_day():
    assert metrics.slope_per_day(points([(1, 72), (2, 71), (3, 70)])) == pytest.approx(-1.0)


def test_slope_needs_two_points_and_time_spread():
    assert metrics.slope_per_day(points([(1, 72)])) is None
    assert metrics.slope_per_day(points([(1, 72), (1, 75)])) is None


def test_perfectly_correlated_series_gives_r_one():
    xs = [float(i) for i in range(10)]
    assert metrics.pearson(xs, [2 * x + 5 for x in xs]) == pytest.approx(1.0)
    assert metrics.pearson(xs, [-x for x in xs]) == pytest.approx(-1.0)


def test_pearson_needs_ten_pairs_and_variance():
    xs = [float(i) for i in range(9)]
    assert metrics.pearson(xs, xs) is None
    ten = [float(i) for i in range(10)]
    assert metrics.pearson(ten, [5.0] * 10) is None
    assert metrics.pearson([5.0] * 10, ten) is None


def test_window_ends_at_the_last_measurement_not_today():
    items = [m(1), m(10), m(14), m(20)]
    # 7 días antes del 20 es el 13: entran el 14 y el 20 (no el 10)
    assert [x["ts"][:10] for x in metrics.window(items, 7)] == ["2026-10-14", "2026-10-20"]
    assert len(metrics.window(items, 30)) == 4


def test_window_includes_the_boundary_and_handles_empty():
    items = [m(13, 12), m(20, 12)]
    assert len(metrics.window(items, 7)) == 2
    assert metrics.window([], 7) == []


def test_stats():
    assert metrics.stats([70, 72, 71]) == {"avg": 71.0, "min": 70.0, "max": 72.0}
    assert metrics.stats([]) is None


@pytest.mark.parametrize(
    "variable,per_day,label",
    [
        ("weight_kg", -0.5, "baja"),
        ("weight_kg", 0.5, "sube"),
        ("weight_kg", 0.01, "estable"),
        ("spo2", 0.0, "estable"),
        ("bpm", 1.0, "sube"),
        ("temp_c", None, None),
    ],
)
def test_trend_label(variable, per_day, label):
    assert metrics.trend_label(variable, per_day) == label


def test_alert_percentage():
    items = [m(1, alert=True), m(2), m(3), m(4)]
    assert metrics.alert_percentage(items) == 25.0
    assert metrics.alert_percentage([]) is None


def test_weight_change():
    items = [m(1, weight_kg=72), m(2, weight_kg=71), m(3, weight_kg=70.8)]
    assert metrics.weight_change(items) == {
        "vs_first_kg": -1.2,
        "vs_first_pct": -1.7,
        "vs_previous_kg": -0.2,
    }
    assert metrics.weight_change(items[:1]) == {
        "vs_first_kg": None,
        "vs_first_pct": None,
        "vs_previous_kg": None,
    }
    assert metrics.weight_change([]) is None

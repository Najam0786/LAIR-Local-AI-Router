from app.hardware.ssd_benchmark import benchmark_ssd_read_speed_gb_s, streaming_viability


def test_real_benchmark_returns_a_positive_read_speed():
    # Real, unmocked: writes and reads back a 64MB temp file.
    speed = benchmark_ssd_read_speed_gb_s()

    assert speed is not None
    assert speed > 0.0


def test_viability_is_zero_for_missing_benchmark():
    assert streaming_viability(None) == 0.0


def test_viability_is_zero_below_the_minimum_bar():
    assert streaming_viability(0.1) == 0.0


def test_viability_is_one_above_the_full_bar():
    assert streaming_viability(10.0) == 1.0


def test_viability_scales_linearly_between_the_bars():
    # Midpoint between 0.3 and 3.0.
    assert 0.4 < streaming_viability(1.65) < 0.6

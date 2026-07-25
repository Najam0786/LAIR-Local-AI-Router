from dataclasses import dataclass

from app.hardware.power import read_power_state


@dataclass
class _FakeBattery:
    percent: float
    power_plugged: bool


def test_no_battery_reports_not_on_battery(monkeypatch):
    import psutil

    monkeypatch.setattr(psutil, "sensors_battery", lambda: None)

    state = read_power_state()

    assert state.on_battery is False
    assert state.battery_percent is None


def test_unplugged_battery_reports_on_battery(monkeypatch):
    import psutil

    monkeypatch.setattr(psutil, "sensors_battery", lambda: _FakeBattery(42.0, False))

    state = read_power_state()

    assert state.on_battery is True
    assert state.battery_percent == 42.0


def test_plugged_in_battery_reports_not_on_battery(monkeypatch):
    import psutil

    monkeypatch.setattr(psutil, "sensors_battery", lambda: _FakeBattery(100.0, True))

    state = read_power_state()

    assert state.on_battery is False
    assert state.battery_percent == 100.0


def test_platform_without_sensors_battery_attribute_is_handled(monkeypatch):
    import psutil

    monkeypatch.delattr(psutil, "sensors_battery", raising=False)

    state = read_power_state()

    assert state.on_battery is False

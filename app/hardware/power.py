import psutil
from pydantic import BaseModel

# Below this estimated footprint, a model counts as "small" for I-15's
# on-battery bias -- deliberately the same threshold I-05's TtlPolicy
# already uses to mean "this machine's fast/generalist role," rather
# than calibrating a second, differently-tuned size cutoff.
BATTERY_SMALL_MODEL_RAM_THRESHOLD_GB = 10.0


class PowerState(BaseModel):
    """
    This machine's current power state (I-15). `battery_percent` is
    `None` on a desktop or wherever `psutil` reports no battery --
    that's a real "no battery" answer, not a missing measurement.
    """

    on_battery: bool
    battery_percent: float | None = None


def read_power_state() -> PowerState:
    """
    Cross-platform (Windows/Linux/macOS -- everywhere `psutil.sensors_battery`
    is implemented) battery read. Desktops, and platforms/psutil builds
    without battery support at all, always report `on_battery=False` --
    the safe default direction (no bias) rather than guessing.
    """

    sensor_fn = getattr(psutil, "sensors_battery", None)

    if sensor_fn is None:
        return PowerState(on_battery=False, battery_percent=None)

    battery = sensor_fn()

    if battery is None:
        return PowerState(on_battery=False, battery_percent=None)

    return PowerState(
        on_battery=not battery.power_plugged,
        battery_percent=battery.percent,
    )

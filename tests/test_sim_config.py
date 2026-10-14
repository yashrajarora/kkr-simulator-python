"""Tests the startup checks on the settings (FR-CAR-6, NFR-C2, NFR-C3, NFR-C4)."""

import pytest

from elevator.config.sim_config import CarSpec, SimConfig, Strategy, TrafficMode

# A regular car on floor 1, capacity 10.
REGULAR = CarSpec(10, 1, 1, None)


def test_rejects_run_without_regular_car():
    """FR-CAR-6: at least one regular car must exist."""
    express = CarSpec(10, 1, 1, {1, 5})

    with pytest.raises(ValueError):
        SimConfig(10, [express], Strategy.ROUND_ROBIN, TrafficMode.NORMAL, None)


def test_rejects_express_car_without_floor_one():
    """FR-CAR-7 / NFR-C4: an express car's served set must include floor 1."""
    express = CarSpec(10, 5, 5, {5, 10})

    with pytest.raises(ValueError):
        SimConfig(10, [REGULAR, express], Strategy.ROUND_ROBIN, TrafficMode.NORMAL, None)


def test_rejects_start_floor_outside_building():
    """NFR-C2: a starting floor outside 1..N is rejected."""
    bad = CarSpec(10, 11, 1, None)

    with pytest.raises(ValueError):
        SimConfig(10, [REGULAR, bad], Strategy.ROUND_ROBIN, TrafficMode.NORMAL, None)

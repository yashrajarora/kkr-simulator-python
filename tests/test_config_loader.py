"""Tests the parking floor check in the settings loader (FR-TRF-4, NFR-C3)."""

import pytest

from elevator.config.config_loader import ConfigLoader
from elevator.config.sim_config import TrafficMode


def _props(mode, **extra):
    """Settings for two cars in the given mode, plus any extra keys."""
    props = {"requests": "r.csv", "strategy": "COST_BASED", "mode": mode, "floors": "10", "cars": "2"}
    props.update(extra)
    return props


@pytest.mark.parametrize("mode", ["EVENING_RUSH", "LUNCH_OUT_RUSH"])
def test_rejects_missing_parking_floor_in_down_rush_modes(mode):
    """FR-TRF-4: every car needs its own parking floor in EVENING_RUSH and LUNCH_OUT_RUSH."""
    props = _props(mode, **{"parkingFloor.1": "10"})

    with pytest.raises(ValueError, match=r"parkingFloor\.2.*FR-TRF-4"):
        ConfigLoader.build(props)


def test_accepts_parking_floor_for_every_car_in_evening_rush():
    """FR-TRF-4: with a parking floor for each car, the evening rush config is built."""
    props = _props("EVENING_RUSH", **{"parkingFloor.1": "10", "parkingFloor.2": "6"})

    config = ConfigLoader.build(props)

    assert config.mode == TrafficMode.EVENING_RUSH
    assert [car.parking_floor for car in config.cars] == [10, 6]


@pytest.mark.parametrize("mode", ["NORMAL", "MORNING_RUSH", "LUNCH_BACK_RUSH"])
def test_missing_parking_floor_defaults_to_floor_one_in_other_modes(mode):
    """The default of floor 1 still applies where the parking floor is not required."""
    config = ConfigLoader.build(_props(mode))

    assert [car.parking_floor for car in config.cars] == [1, 1]

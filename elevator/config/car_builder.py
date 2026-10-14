"""Turns the car settings into cars for a run (FR-CAR-1, FR-CAR-9, FR-TRF-3 to FR-TRF-5)."""

from elevator.config.sim_config import CarSpec, SimConfig, TrafficMode
from elevator.model.car import Car


def build_cars(config: SimConfig) -> list[Car]:
    """Builds every car in car-number order (FR-CAR-1, FR-CAR-9, FR-TRF-3 to FR-TRF-5).

    Args:
        config: the settings for the run.

    Returns:
        the cars, car 1 first.
    """
    cars = []
    for index, spec in enumerate(config.cars):
        parking_floor = _parking_floor_for(spec, config.mode)
        cars.append(Car(index + 1, spec.start_floor, spec.capacity, spec.served_floors, parking_floor))
    return cars


def _parking_floor_for(spec: CarSpec, mode: TrafficMode) -> int | None:
    """Which floor an empty car waits on in this traffic mode (FR-TRF-3, FR-TRF-4, FR-TRF-5).

    Args:
        spec: the car's settings.
        mode: the traffic mode.

    Returns:
        the parking floor, or None in NORMAL mode where the car stays where it stopped.
    """
    match mode:
        case TrafficMode.NORMAL:
            return None
        case TrafficMode.MORNING_RUSH | TrafficMode.LUNCH_BACK_RUSH:
            return 1
        case TrafficMode.LUNCH_OUT_RUSH | TrafficMode.EVENING_RUSH:
            return spec.parking_floor

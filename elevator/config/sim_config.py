"""All startup settings for one run (NFR-C1 to NFR-C4)."""

from dataclasses import dataclass
from enum import Enum


class Strategy(Enum):
    """Assignment algorithms (FR-ASN-4a, 4b, 4c).

    NEAREST_CAR_SIMPLE is the floor-distance comparison (FR-ASN-4b-S).
    """

    ROUND_ROBIN = "ROUND_ROBIN"
    NEAREST_CAR = "NEAREST_CAR"
    NEAREST_CAR_FORWARD_RUN = "NEAREST_CAR_FORWARD_RUN"
    NEAREST_CAR_SIMPLE = "NEAREST_CAR_SIMPLE"
    COST_BASED = "COST_BASED"
    BALANCED_STRATEGY = "BALANCED_STRATEGY"


class TrafficMode(Enum):
    """Traffic modes (FR-TRF-1)."""

    NORMAL = "NORMAL"
    MORNING_RUSH = "MORNING_RUSH"
    LUNCH_OUT_RUSH = "LUNCH_OUT_RUSH"
    LUNCH_BACK_RUSH = "LUNCH_BACK_RUSH"
    EVENING_RUSH = "EVENING_RUSH"


@dataclass(frozen=True)
class CarSpec:
    """Startup settings for one car (FR-CAR-1, FR-CAR-3, FR-CAR-9).

    Attributes:
        capacity: maximum riders (FR-CAR-1).
        start_floor: floor the car starts on (FR-CAR-9).
        parking_floor: floor used in LUNCH_OUT_RUSH and EVENING_RUSH (NFR-C3).
        served_floors: allowed floors for an express car, or None for a regular car (FR-CAR-3).
    """

    capacity: int
    start_floor: int
    parking_floor: int
    served_floors: set[int] | None


@dataclass(frozen=True)
class SimConfig:
    """All startup settings for one run (NFR-C1 to NFR-C4). Built by ConfigLoader.

    The checks in __post_init__ run when the config is made, so an invalid run never starts
    (NFR-C2, NFR-C3, NFR-C4).

    Attributes:
        floors: number of floors N, numbered 1 to N (FR-FLR-1, NFR-C1).
        cars: one entry per car, in car-number order.
        strategy: assignment algorithm for the whole run (FR-ASN-4).
        mode: traffic mode for the whole run (FR-TRF-1, FR-TRF-2).
        requests_file: name of the request resource to read, such as "requests.csv" (FR-IN-1, NFR-I1).
    """

    floors: int
    cars: list[CarSpec]
    strategy: Strategy
    mode: TrafficMode
    requests_file: str | None

    def __post_init__(self) -> None:
        """Checks the settings. Raises ValueError with a message that names the problem."""
        if self.floors < 1:
            raise ValueError("floors must be at least 1")
        if not self.cars:
            raise ValueError("at least one car is required")
        # FR-CAR-6: a regular car serves every floor, so FR-FLR-2 (every floor served) also holds.
        if not any(car.served_floors is None for car in self.cars):
            raise ValueError("at least one regular car is required (FR-CAR-6)")
        for number, car in enumerate(self.cars, start=1):
            _check_car(self.floors, number, car)


def _check_car(floors: int, number: int, car: CarSpec) -> None:
    """Checks one car's settings (FR-CAR-9, NFR-C2, NFR-C3, NFR-C4).

    Args:
        floors: number of floors N.
        number: car number, 1-based, used in messages.
        car: the car's settings.

    Raises:
        ValueError: if a setting is out of range or an express car's settings are not valid.
    """
    if car.capacity < 1:
        raise ValueError(f"car {number}: capacity must be at least 1")
    _check_floor(floors, number, "start floor", car.start_floor)
    _check_floor(floors, number, "parking floor", car.parking_floor)
    # A regular car has no served set, so there is nothing more to check.
    if car.served_floors is None:
        return
    # NFR-C4: an express car's served set must be non-empty, include floor 1, and stay in 1..N.
    if not car.served_floors or 1 not in car.served_floors:
        raise ValueError(f"car {number}: served floors must include floor 1 (FR-CAR-7)")
    for floor in car.served_floors:
        _check_floor(floors, number, "served floor", floor)
    # NFR-C2, NFR-C3: start and parking floors of an express car must be in its served set.
    if car.start_floor in car.served_floors and car.parking_floor in car.served_floors:
        return
    raise ValueError(f"car {number}: start and parking floors must be in its served floors")


def _check_floor(floors: int, number: int, what: str, floor: int) -> None:
    """Checks that a floor is in 1..N (NFR-C1, NFR-C2, NFR-C3).

    Args:
        floors: number of floors N.
        number: car number, used in messages.
        what: which setting is being checked, used in messages.
        floor: the floor to check.

    Raises:
        ValueError: if the floor is outside 1..N.
    """
    if 1 <= floor <= floors:
        return
    raise ValueError(f"car {number}: {what} {floor} is outside floors 1 to {floors}")

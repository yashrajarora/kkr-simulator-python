"""Direction of travel of a car, or of a passenger's trip (FR-CAR-2)."""

from enum import Enum


class Direction(Enum):
    """Direction of travel of a car, or of a passenger's trip.

    A car has IDLE when it is not moving: at its parking floor with no riders or unboarded
    passengers (FR-CAR-2).
    """

    UP = "UP"
    DOWN = "DOWN"
    IDLE = "IDLE"

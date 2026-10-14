"""Tests the floor-based Nearest Car strategy, which takes the car's direction into account (FR-ASN-4b)."""

from elevator.dispatch.nearest_car_strategy import NearestCarStrategy
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


def test_car_heading_away_is_not_ready_so_idle_car_gets_the_request():
    """Car 1 is going UP with a passenger, so it cannot take a passenger at floor 1 going UP without turning
    around. Car 2 is idle, so it is ready and gets the request, even though it is farther away."""
    heading_away = Car(1, 2, 10, None, None)
    heading_away.add_trip(Trip(PassengerRequest(0, "rider", 5, 9)))
    idle = Car(2, 4, 10, None, None)

    chosen = NearestCarStrategy().choose_best_car_by_strategy(PassengerRequest(0, "p", 1, 2), [heading_away, idle])

    assert chosen is idle


def test_car_heading_toward_passenger_is_measured_directly():
    """Car 1 is going UP toward a passenger at floor 6, so a passenger at floor 4 going UP is on its way: 2 floors.
    Car 2 is idle 3 floors away and also ready. Car 1 is nearer, so it gets the request."""
    heading_toward = Car(1, 2, 10, None, None)
    heading_toward.add_trip(Trip(PassengerRequest(0, "rider", 6, 9)))
    idle = Car(2, 7, 10, None, None)

    chosen = NearestCarStrategy().choose_best_car_by_strategy(PassengerRequest(0, "p", 4, 5), [heading_toward, idle])

    assert chosen is heading_toward

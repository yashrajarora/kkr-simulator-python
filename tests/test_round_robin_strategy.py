"""Tests Round Robin's grouping by direction (FR-ASN-4a, FR-ASN-3)."""

from elevator.dispatch.round_robin_strategy import RoundRobinStrategy
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


def test_same_direction_passenger_joins_car_already_going_that_way():
    """A car already planned to go UP takes a second UP passenger, even though the next car in rotation is idle."""
    first = Car(1, 1, 10, None, None)
    first.add_trip(Trip(PassengerRequest(0, "passenger1", 1, 51)))
    second = Car(2, 1, 10, None, None)

    strategy = RoundRobinStrategy()
    newcomer = PassengerRequest(0, "passenger2", 1, 37)

    assert strategy.choose_best_car_by_strategy(newcomer, [first, second]) is first


def test_ready_idle_car_is_chosen_before_other_direction_car():
    """The first car is going UP, so it is not ready for a DOWN passenger. The idle second car is ready, so it
    takes the passenger."""
    first = Car(1, 1, 10, None, None)
    first.add_trip(Trip(PassengerRequest(0, "passenger1", 1, 51)))
    second = Car(2, 1, 10, None, None)

    strategy = RoundRobinStrategy()
    down = PassengerRequest(1, "passenger3", 20, 1)

    assert strategy.choose_best_car_by_strategy(down, [first, second]) is second


def test_no_ready_car_falls_back_to_rotation_car():
    """No car is ready for a DOWN passenger, since both are going UP. Round Robin then takes the next car in
    rotation, which is the first car, and the passenger waits on it."""
    first = Car(1, 1, 10, None, None)
    first.add_trip(Trip(PassengerRequest(0, "passenger1", 1, 51)))
    second = Car(2, 1, 10, None, None)
    second.add_trip(Trip(PassengerRequest(0, "passenger2", 1, 51)))

    strategy = RoundRobinStrategy()
    down = PassengerRequest(1, "passenger3", 20, 1)

    assert strategy.choose_best_car_by_strategy(down, [first, second]) is first

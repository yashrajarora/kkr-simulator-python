"""Tests the Balanced strategy's trade-off between pickup time and load (FR-ASN-4d)."""

from elevator.dispatch.balanced_strategy import BalancedStrategy
from elevator.dispatch.trip_estimator import TripEstimator
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


def test_nearer_car_wins_when_loads_are_equal():
    """With no passengers on either car, the car that reaches the passenger sooner gets the request."""
    near = Car(1, 4, 10, None, None)
    far = Car(2, 1, 10, None, None)
    strategy = BalancedStrategy(TripEstimator(10))

    assert strategy.choose_best_car_by_strategy(PassengerRequest(0, "p", 5, 9), [near, far]) is near


def test_lighter_car_wins_when_it_is_only_slightly_farther():
    """The near car already has two passengers, so its load outweighs the one extra step the far car needs."""
    near = Car(1, 4, 10, None, None)
    near.add_trip(Trip(PassengerRequest(0, "a", 4, 9)))
    near.add_trip(Trip(PassengerRequest(0, "b", 4, 8)))
    far = Car(2, 6, 10, None, None)
    strategy = BalancedStrategy(TripEstimator(10))

    assert strategy.choose_best_car_by_strategy(PassengerRequest(0, "p", 5, 1), [near, far]) is far

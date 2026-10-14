"""Tests Nearest Car (FR-ASN-4b) with express cars (NFR-TS3)."""

from elevator.dispatch.nearest_car_forward_run_strategy import NearestCarForwardRunStrategy
from elevator.dispatch.trip_estimator import TripEstimator
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest


def test_request_outside_express_served_set_is_never_assigned_to_express_car():
    """An express car at floor 2 serves floors 1, 2 and 10. A passenger from floor 1 to floor 10 is served by it,
    and it is nearer than the regular car at floor 20. A passenger from floor 3 to floor 4 is nearer to the
    express car, but it is outside the express car's served set, so the regular car takes them (NFR-TS3)."""
    estimator = TripEstimator(20)
    express = Car(1, 2, 4, {1, 2, 10}, 2)
    regular = Car(2, 20, 4, None, None)
    cars = [express, regular]
    strategy = NearestCarForwardRunStrategy(estimator)

    assert strategy.choose_best_car_by_strategy(PassengerRequest(0, "served", 1, 10), cars) is express
    assert strategy.choose_best_car_by_strategy(PassengerRequest(0, "skipped", 3, 4), cars) is regular

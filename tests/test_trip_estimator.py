"""Tests the forward run for a full car going UP (FR-ASN-5, NFR-S1)."""

from elevator.dispatch.trip_estimator import TripEstimator
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


def add_and_board(car: Car, request: PassengerRequest) -> None:
    """Puts a passenger on the car at time 0, as if the car had already picked them up.

    Args:
        car: the car.
        request: the passenger's request.
    """
    trip = Trip(request)
    car.add_trip(trip)
    car._board(0)


def test_full_car_picks_up_when_a_rider_gets_off_first():
    """A car of capacity 2 going UP with two riders, one of whom gets off at floor 4. A new passenger at floor 6
    is picked up as soon as the seat is free and the car reaches floor 6 (time 5)."""
    estimator = TripEstimator(20)
    car = Car(1, 1, 2, None, None)
    add_and_board(car, PassengerRequest(0, "rider1", 1, 10))
    add_and_board(car, PassengerRequest(0, "rider2", 1, 4))

    trips = estimator.predict_trips(car, PassengerRequest(0, "newcomer", 6, 9))

    assert trips[-1].pickup_time == 5


def test_full_car_does_not_pick_up_until_seat_frees():
    """A car of capacity 2 going UP with two riders, both getting off at floor 10. The new passenger at floor 6
    cannot board while the car is full. The car drops both riders at floor 10, comes back down to floor 6, and
    picks the passenger up at time 13."""
    estimator = TripEstimator(20)
    car = Car(1, 1, 2, None, None)
    add_and_board(car, PassengerRequest(0, "rider1", 1, 10))
    add_and_board(car, PassengerRequest(0, "rider2", 1, 10))

    trips = estimator.predict_trips(car, PassengerRequest(0, "newcomer", 6, 9))

    assert trips[-1].pickup_time == 13


def test_pickup_waits_for_seat_when_car_is_full():
    """A car of capacity 1 going UP with one rider, who gets off at floor 10. A new passenger at floor 3 cannot
    board until the rider gets off. The car drops the rider at floor 10, comes back down to floor 3, and picks
    the passenger up then (FR-ASN-5)."""
    estimator = TripEstimator(20)
    car = Car(1, 1, 1, None, None)
    add_and_board(car, PassengerRequest(0, "rider", 1, 10))

    pickup = estimator.predict_pickup_time(car, PassengerRequest(0, "newcomer", 3, 5))

    assert pickup == 16

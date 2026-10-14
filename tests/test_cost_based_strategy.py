"""Tests Cost Based (FR-ASN-4c), using the forward run."""

from elevator.dispatch.cost_based_strategy import CostBasedStrategy
from elevator.dispatch.trip_estimator import TripEstimator
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


def test_picks_car_that_does_not_delay_passenger_already_waiting():
    """Car 1 is at floor 1 and already has a passenger waiting at floor 9. A new passenger at floor 2 is nearest
    to car 1, but putting them on car 1 would make the waiting passenger wait longer (8 steps). Car 2 at floor 4
    gives the new passenger a wait of 2 and nobody else on the car waits, so the largest wait is 2 and Cost Based
    picks car 2. Nearest Car would pick car 1."""
    estimator = TripEstimator(30)
    car1 = Car(1, 1, 2, None, None)
    car1.add_trip(Trip(PassengerRequest(0, "waiting", 9, 10)))
    car2 = Car(2, 4, 2, None, None)
    cars = [car1, car2]

    strategy = CostBasedStrategy(estimator)
    chosen = strategy.choose_best_car_by_strategy(PassengerRequest(0, "newcomer", 2, 5), cars)

    assert chosen is car2


def test_picks_car_whose_full_riders_leave_sooner_when_both_cars_are_full():
    """Both cars are full with a rider who gets off at floor 9, so the new passenger can board only after that
    rider leaves. Car 1 has to drop its rider at floor 9 and come all the way back down to floor 2, so the new
    passenger waits 14 steps. Car 2 drops its rider at floor 9 sooner and reaches floor 2 at step 10, so its
    largest wait is 10. Cost Based picks car 2."""
    estimator = TripEstimator(30)
    car1 = Car(1, 2, 1, None, None)
    car1.add_trip(Trip(PassengerRequest(0, "rider1", 2, 9)))
    car1._board(0)
    car2 = Car(2, 6, 1, None, None)
    car2.add_trip(Trip(PassengerRequest(0, "rider2", 6, 9)))
    car2._board(0)
    cars = [car1, car2]

    strategy = CostBasedStrategy(estimator)
    assert strategy.choose_best_car_by_strategy(PassengerRequest(0, "newcomer", 2, 5), cars) is car2

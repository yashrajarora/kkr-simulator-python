"""Balanced (FR-ASN-4d): trades off pickup time against the number of passengers a car already has.

Each car is scored as wait_time_weight x (wait in ticks until pickup) + car_load_weight x (riders and unboarded passengers).
The car with the lowest score gets the request. A wait_time_weight alone gives Nearest Car, and a car_load_weight alone
spreads passengers across cars.
Ties go to the lower car number, because only a strictly lower score replaces the current best.
"""

from elevator.dispatch.dispatch_strategy import DispatchStrategy
from elevator.dispatch.trip_estimator import TripEstimator
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest


class BalancedStrategy(DispatchStrategy):
    """Balanced (FR-ASN-4d): picks the car with the lowest score of pickup time and load."""

    def __init__(self, estimator: TripEstimator, wait_time_weight: float = 1.0, car_load_weight: float = 1.0):
        """Args:
            estimator: predicts when each car would pick the passenger up.
            wait_time_weight: weight of the wait in ticks before pickup.
            car_load_weight: weight of the passengers the car already carries (riders and unboarded).
        """
        self._estimator = estimator
        self._wait_time_weight = wait_time_weight
        self._car_load_weight = car_load_weight

    def choose_best_car_by_strategy(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """Returns the car with the lowest score (FR-ASN-4d).

        Args:
            request: the new request.
            cars: all cars, in car-number order.

        Returns:
            the car with the lowest score, or None if no car is eligible.
        """
        best_car = None
        best_score = float("inf")
        for car in cars:
            pickup_time = self._estimator.predict_pickup_time(car, request)
            if pickup_time is not None:
                wait_time = pickup_time - request.request_time
                score = (self._wait_time_weight * wait_time
                         + self._car_load_weight * len(car.all_trips))
                if score < best_score:
                    best_car = car
                    best_score = score
        return best_car

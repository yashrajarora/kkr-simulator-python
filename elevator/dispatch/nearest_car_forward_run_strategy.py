"""Nearest Car forward run (FR-ASN-4b).

Gives the request to the car that reaches the passenger first. The distance is the number of
time steps until pickup, from the forward run, so stops, seats and turns all count. Ties go to
the lower car number, because cars are checked in order and only a strictly smaller distance
replaces the current best.
"""

from elevator.dispatch.dispatch_strategy import DispatchStrategy
from elevator.dispatch.trip_estimator import TripEstimator
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest


class NearestCarForwardRunStrategy(DispatchStrategy):
    """Nearest Car (FR-ASN-4b): gives the request to the car that reaches the passenger first."""

    def __init__(self, estimator: TripEstimator):
        """Args:
            estimator: predicts when each car would pick the passenger up.
        """
        self._estimator = estimator

    def choose_best_car_by_strategy(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """Returns the car that picks the passenger up soonest (FR-ASN-4b).

        Args:
            request: the new request.
            cars: all cars, in car-number order.

        Returns:
            the nearest car, or None if no car is eligible.
        """
        nearest_car = None
        nearest_distance = float("inf")
        for car in cars:
            # The time this car picks the passenger up. None means the car is not eligible.
            pickup_time = self._estimator.predict_pickup_time(car, request)
            if pickup_time is not None:
                # Time steps from the request time until this car picks the passenger up.
                distance = pickup_time - request.request_time
                # Keep this car if it is the nearest so far. Ties keep the earlier car.
                if distance < nearest_distance:
                    nearest_car = car
                    nearest_distance = distance
        return nearest_car

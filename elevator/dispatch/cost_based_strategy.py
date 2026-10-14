"""Cost Based (FR-ASN-4c): keeps waits fair so no passenger is left far behind.

For each car, the predicted trips give the wait of the new passenger and of everyone already on
the car. The car's largest wait is the longest of these waits. The car with the smallest largest
wait wins. Ties go to the lower car number, because only a strictly better car replaces the
current best.
"""

from elevator.dispatch.dispatch_strategy import DispatchStrategy
from elevator.dispatch.trip_estimator import TripEstimator
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


class CostBasedStrategy(DispatchStrategy):
    """Cost Based (FR-ASN-4c): picks the car whose longest predicted wait is shortest."""

    def __init__(self, estimator: TripEstimator):
        """Args:
            estimator: checks each car and predicts its trips.
        """
        self._estimator = estimator

    def choose_best_car_by_strategy(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """Returns the car with the smallest largest predicted wait (FR-ASN-4c).

        Args:
            request: the new request.
            cars: all cars, in car-number order.

        Returns:
            the chosen car, or None if no car is eligible.
        """
        return self._fairest_of(cars, request)

    def _fairest_of(self, group: list[Car], request: PassengerRequest) -> Car | None:
        """The eligible car with the smallest largest wait in a group of cars.

        Args:
            group: the cars to look at, in car-number order.
            request: the new request.

        Returns:
            the car with the smallest largest wait, or None if no car in the group is eligible.
        """
        fairest_car = None
        fairest_wait = float("inf")
        for car in group:
            # The predicted trips for this car, with the new request last. Empty means the car is not eligible.
            predicted_trips = self._estimator.predict_trips(car, request)
            if predicted_trips:
                # The longest wait of anyone on this car after the assignment, including the new passenger.
                longest_wait = self._longest_wait(predicted_trips)
                # Keep this car if its largest wait is the smallest so far. Ties keep the earlier car.
                if longest_wait < fairest_wait:
                    fairest_car = car
                    fairest_wait = longest_wait
        return fairest_car

    @staticmethod
    def _longest_wait(predicted_trips: list[Trip]) -> int:
        """The longest wait among the trips: the new passenger and everyone already on the car.

        Args:
            predicted_trips: the predicted trips.

        Returns:
            the largest wait time, never negative.
        """
        # Start at 0 and keep the largest wait seen, so the result is never negative.
        max_wait = 0
        for trip in predicted_trips:
            max_wait = max(max_wait, trip.wait_time)
        return max_wait

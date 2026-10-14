"""Nearest Car, simplified (comparison only).

It measures distance in floors from the car to the passenger, so it does not meet FR-ASN-4b, which measures
time steps. A car that can take the passenger now (room, and idle or going the passenger's way with the
passenger ahead, FR-ASN-3) always beats a car that cannot. A car that cannot still gets the passenger if no
car can take them now, so the passenger always gets a car. Ties go to the lower car number.
"""

from elevator.dispatch.dispatch_strategy import DispatchStrategy
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest


class NearestCarSimpleStrategy(DispatchStrategy):
    """Nearest Car, simplified (FR-ASN-4b-S, comparison only)."""

    def choose_best_car_by_strategy(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """Returns the nearest car in floors, preferring cars that can take the passenger now.

        Args:
            request: the new request.
            cars: all cars, in car-number order.

        Returns:
            the nearest car, or None if no car serves both floors of the request.
        """
        candidates = [car for car in cars if car.can_serve_request_floors(request)]
        ready = [car for car in candidates if car.can_honor_elevator_constraints(request.source, request.direction)]
        pool = ready or candidates
        if not pool:
            return None
        return min(pool, key=lambda car: abs(car.current_floor - request.source))

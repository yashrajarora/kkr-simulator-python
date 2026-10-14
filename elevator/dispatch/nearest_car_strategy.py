"""Nearest Car (FR-ASN-4b), measured in floors with the car's direction taken into account.

A car that is heading toward the passenger is measured by the floors to the passenger. A car that is heading
away must first reach its turn point, the furthest floor it is committed to in its direction, and then come back.
Only cars with room for the passenger now are measured, unless no eligible car has room. Ties go to the lower car
number, because cars are checked in order and only a strictly smaller distance replaces the current best.

This is an estimate. It ignores stops, seats and the time spent at each floor. NEAREST_CAR_FORWARD_RUN is the exact
version.
"""

from elevator.dispatch.dispatch_strategy import DispatchStrategy
from elevator.model.car import Car
from elevator.model.direction import Direction
from elevator.model.passenger_request import PassengerRequest
from elevator.simulator import movement


class NearestCarStrategy(DispatchStrategy):
    """Nearest Car (FR-ASN-4b): the car nearest to the passenger in floors, with its direction taken into account."""

    def choose_best_car_by_strategy(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """Returns the nearest car in floors, among cars with room now (FR-ASN-4b).

        Args:
            request: the new request.
            cars: all cars, in car-number order.

        Returns:
            the nearest car, or None if no car serves both floors of the request.
        """
        candidates = [car for car in cars if car.can_serve_request_floors(request)]
        # Filter first: only cars with room now are measured. If none has room, the passenger waits for a seat (FR-ASN-5).
        with_room = [car for car in candidates if car.has_room_for(1)]
        pool = with_room or candidates
        if not pool:
            return None
        return min(pool, key=lambda car: self._floor_distance(car, request.source))

    @staticmethod
    def _floor_distance(car: Car, source: int) -> int:
        """The floors the car must travel to reach the passenger's floor, with any turn-around (FR-CAR-8).

        Args:
            car: the car.
            source: the floor the passenger starts from.

        Returns:
            the number of floors to the passenger, plus the detour to the turn point if the car is heading away.
        """
        floor = car.current_floor
        direction = car.next_direction()
        if direction == Direction.IDLE or movement.is_ahead(floor, direction, source):
            return abs(floor - source)
        ahead = [trip_floor for trip in car.all_trips for trip_floor in (trip.source, trip.destination)
                 if movement.is_ahead(floor, direction, trip_floor)]
        if not ahead:
            return abs(floor - source)
        turn_floor = max(ahead) if direction == Direction.UP else min(ahead)
        return abs(floor - turn_floor) + abs(turn_floor - source)

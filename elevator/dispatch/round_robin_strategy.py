"""Round Robin (FR-ASN-4a), with grouping of same-time requests by direction.

First, the passenger goes to the first car that is already going the passenger's direction and
can take them, so passengers going the same way share a car (FR-ASN-3). If no such car exists,
the passenger goes to the next eligible car in rotation, as Round Robin does. The rotation
pointer moves only for rotation picks.

Round Robin does not score cars.
"""

from elevator.dispatch.dispatch_strategy import DispatchStrategy
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest


class RoundRobinStrategy(DispatchStrategy):
    """Round Robin (FR-ASN-4a), with grouping of same-time requests by direction."""

    def __init__(self):
        """Starts the rotation at the first car."""
        # Index of the car to try first for the next rotation pick.
        self._next = 0

    def choose_best_car_by_strategy(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """Chooses the car for the request (FR-ASN-4a, FR-ASN-3).

        Three passes, each starting at the rotation pointer:
            1. a car that is ready now (room, and idle or going the passenger's way with the
               passenger ahead of it);
            2. a car with room, whatever its direction, since it will turn around;
            3. any car that reaches both floors.

        The passenger waits on the chosen car until they can board.

        Args:
            request: the new request.
            cars: all cars, in car-number order.

        Returns:
            the chosen car.
        """
        ready = self._next_ready_car(request, cars)
        if ready is not None:
            return ready
        with_room = self._next_car_with_room(request, cars)
        if with_room is not None:
            return with_room
        return self._next_car_reaching_floors(request, cars)

    def group_for(self, car: Car, request: PassengerRequest,
                  waiting: list[PassengerRequest]) -> list[PassengerRequest]:
        """The requests that go to the car together with this one (FR-ASN-4a).

        Those made at the same time in the same direction, if the car has room for all of them and
        can finish them. Otherwise the request goes alone.

        Args:
            car: the car chosen for the request.
            request: the request chosen first.
            waiting: the requests made at this time that are not yet assigned.

        Returns:
            the group, with the request first.
        """
        group = [request]
        for other in waiting:
            # Identity check (is not), so the request is not added to its own group.
            if other is not request and other.direction == request.direction:
                group.append(other)
        if len(group) > 1 and self._group_fits(car, group):
            return group
        return [request]

    @staticmethod
    def _group_fits(car: Car, group: list[PassengerRequest]) -> bool:
        """Whether the car can take the whole group at once (FR-ASN-4a, FR-CAR-4).

        It needs a free seat for every passenger, and it must reach both floors of every request.

        Args:
            car: the car chosen for the request.
            group: the requests in the group.

        Returns:
            True if the car can take all of them.
        """
        fits = car.has_room_for(len(group))
        for passenger in group:
            fits = fits and car.can_serve_floor(passenger.source) and car.can_serve_floor(passenger.destination)
        return fits

    def _next_ready_car(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """The next car in rotation that is ready now (FR-ASN-3, NFR-S1).

        It reaches both floors, has room, and is idle or going the passenger's way with the
        passenger ahead. The rotation pointer moves past it.

        Returns:
            the car, or None if none is ready.
        """
        for k in range(len(cars)):
            index = (self._next + k) % len(cars)
            car = cars[index]
            reaches_both_floors = car.can_serve_request_floors(request)
            ready_now = car.can_honor_elevator_constraints(request.source, request.direction)
            if reaches_both_floors and ready_now:
                self._next = (index + 1) % len(cars)
                return car
        return None

    def _next_car_with_room(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """The next car in rotation that reaches both floors and has room, whatever its direction.

        The rotation pointer moves past it.

        Returns:
            the car, or None if none has room.
        """
        for k in range(len(cars)):
            index = (self._next + k) % len(cars)
            car = cars[index]
            reaches_both_floors = car.can_serve_request_floors(request)
            has_room = car.has_room_for(1)
            if reaches_both_floors and has_room:
                self._next = (index + 1) % len(cars)
                return car
        return None

    def _next_car_reaching_floors(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """The next car in rotation that reaches both floors, whatever its direction or room.

        The rotation pointer moves past it.

        Returns:
            the car, or None if no car reaches both floors.
        """
        for k in range(len(cars)):
            index = (self._next + k) % len(cars)
            car = cars[index]
            if car.can_serve_request_floors(request):
                self._next = (index + 1) % len(cars)
                return car
        return None

"""One elevator car (FR-CAR-1 to FR-CAR-9)."""

import logging

from elevator.model.direction import Direction
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip
from elevator.simulator import movement

# Logger for the car's real boardings and drop-offs. Only real cars log (see _real_car).
LOGGER = logging.getLogger(__name__)


class Car:
    """One elevator car (FR-CAR-1 to FR-CAR-9).

    The car keeps two lists of trips:
        active_trips: trips whose passenger is inside the car (riders).
        unboarded_trips: trips assigned to this car whose passenger has not got on yet.

    A trip moves from unboarded to active when its passenger boards, and is removed when the
    passenger gets off. The movement rules are in simulator.movement.
    """

    def __init__(self, car_id: int, current_floor: int, capacity: int,
                 served_floors: set[int] | None, parking_floor: int | None):
        """Creates a car. Called by config.car_builder.build_cars.

        Args:
            car_id: 1-based car number, used for ties and output (NFR-T1).
            current_floor: starting floor (FR-CAR-9).
            capacity: maximum riders (FR-CAR-1).
            served_floors: floors an express car may stop at, or None for a regular car (FR-CAR-3).
            parking_floor: floor to wait on when empty, or None in NORMAL mode (FR-TRF-3, FR-TRF-4).
        """
        self._id = car_id
        # True for the real car, False for a copy used in a forward run. Only the real car logs and counts travel.
        self._real_car = True
        self._current_floor = current_floor
        # Floors moved so far, up or down (FR-OUT-3).
        self._floors_travelled = 0
        self._capacity = capacity
        self._served_floors = served_floors
        self._parking_floor = parking_floor
        self._active_trips: list[Trip] = []
        self._unboarded_trips: list[Trip] = []
        # The direction the car is travelling in, or was last sent toward a passenger (FR-CAR-8). It is set when
        # a passenger joins a car with no unboarded trips, and overwritten by each move. It is kept after the
        # riders get off, so the car can still turn around from it.
        self._travel_direction = Direction.IDLE

    def can_serve_floor(self, floor: int) -> bool:
        """Whether this car may stop at a floor (FR-CAR-4, express cars stop only at their served floors).

        Args:
            floor: the floor to check.

        Returns:
            True for a regular car, or if the floor is in the express car's served set.
        """
        # A regular car has no served set, so it serves every floor.
        if self._served_floors is None:
            return True
        return floor in self._served_floors

    def can_serve_request_floors(self, request: PassengerRequest) -> bool:
        """Whether this car serves both floors of a request (FR-CAR-4).

        Args:
            request: the request to check.

        Returns:
            True if the car may stop at the request's source and at its destination.
        """
        return self.can_serve_floor(request.source) and self.can_serve_floor(request.destination)

    @property
    def is_express(self) -> bool:
        """Whether this is an express car, which serves only its own floors (FR-CAR-3)."""
        return self._served_floors is not None

    def add_trip(self, trip: Trip) -> None:
        """Adds a trip that has just been assigned to this car. It starts as an unboarded trip.

        Implements FR-ASN-1 (each request is assigned to one car). Called by RequestQueue.assign_car.

        Args:
            trip: the trip assigned to this car.
        """
        if not self._unboarded_trips:
            self._travel_direction = movement.heading_for_new_trip(self._current_floor, trip.source)
        self._unboarded_trips.append(trip)

    def has_room_for(self, count: int) -> bool:
        """Whether the car has room for this many more trips (FR-ASN-5, NFR-S1).

        Riders and unboarded trips both count against the capacity.

        Args:
            count: the number of new trips.

        Returns:
            True if riders plus unboarded trips plus count is at most the capacity.
        """
        return len(self._active_trips) + len(self._unboarded_trips) + count <= self._capacity

    @property
    def active_trips(self) -> list[Trip]:
        """Trips whose passenger is inside the car (FR-ASN-3).

        Returns:
            a new list of riders, in boarding order.
        """
        return list(self._active_trips)

    @property
    def all_trips(self) -> list[Trip]:
        """All trips on this car, riders first, then unboarded trips (FR-ASN-4).

        Planning needs every trip, so it can check who is still on the car.

        Returns:
            a new list holding the same trip objects.
        """
        return self._active_trips + self._unboarded_trips

    def can_honor_elevator_constraints(self, source: int, wanted: Direction) -> bool:
        """Whether the car can take a passenger now (FR-ASN-3, NFR-S1).

        The car needs room, and it must be idle or going the passenger's way with the passenger
        ahead of it. For an UP trip the passenger's floor must be at or above the car; for a DOWN
        trip, at or below it.

        Args:
            source: the floor the passenger starts from.
            wanted: the direction of the passenger's trip.

        Returns:
            True if the car can take the passenger without turning around.
        """
        if not self.has_room_for(1):
            return False
        # An empty car, even one heading to parking, takes a passenger going either way.
        if not self._active_trips and not self._unboarded_trips:
            return True
        return self._travel_direction == wanted and movement.is_ahead(self._current_floor, wanted, source)

    def _move_one_floor(self) -> None:
        """Moves the car at most one floor in this time step (FR-TIM-2, FR-TIM-6 step 4).

        A car with no direction stays where it is. An express car never stops outside its served set
        (FR-CAR-4, NFR-S5). Boarding happens before this in run_step, so a car that has a waiting passenger
        on its floor has riders by the time it moves.
        """
        floor_before = self._current_floor
        self._travel_direction = self.next_direction()
        if self._travel_direction != Direction.IDLE:
            self._current_floor = movement.step_toward(self._current_floor, self._travel_direction)
        # Count only real travel, not the moves of a forward-run copy (FR-OUT-3).
        if self._real_car:
            self._floors_travelled += abs(self._current_floor - floor_before)

    def next_direction(self) -> Direction:
        """The direction the car moves in this step (FR-ASN-3, FR-CAR-8, FR-TRF-3 to FR-TRF-5).

        With riders, the car goes in their direction, since they all go the same way. With unboarded passengers,
        the LOOK policy decides, with their floors as targets. An empty car heads for its parking floor.

        Returns:
            UP, DOWN, or IDLE.
        """
        if self._active_trips:
            return self._active_trips[0].direction
        if self._unboarded_trips:
            floors = [trip.source for trip in self._unboarded_trips]
            return movement.unboarded_trip_direction(
                self._travel_direction,
                unboarded_floors_above=any(floor >= self._current_floor for floor in floors),
                unboarded_floors_below=any(floor <= self._current_floor for floor in floors))
        return movement.parking_direction(self._current_floor, self._parking_target())

    @property
    def floors_travelled(self) -> int:
        """The number of floors this car has moved so far, up or down (FR-OUT-3)."""
        return self._floors_travelled

    def _parking_target(self) -> int:
        """The floor an empty car with no unboarded trips waits on (FR-TRF-3 to FR-TRF-5).

        Returns:
            the parking floor, or the current floor if none is set.
        """
        if self._parking_floor is not None:
            return self._parking_floor
        return self._current_floor

    def run_step(self, time: int) -> None:
        """Runs this car's part of one time step, in the order of FR-TIM-6: riders get off, passengers get
        on, and then the car moves one floor. The real run and the forward run both use this, so their
        steps always match.

        Args:
            time: the current time step.
        """
        self._alight(time)
        self._board(time)
        self._move_one_floor()

    def _alight(self, time: int) -> None:
        """Drops off the riders whose destination is this floor (FR-TIM-6 step 3, FR-ASN-3).

        Riders get off before passengers get on.

        Args:
            time: the current time step, recorded as the drop-off time.
        """
        # Loop over a copy, because the rider list changes as riders get off.
        for trip in self.active_trips:
            if trip.destination == self._current_floor:
                trip.mark_drop(time)
                self._active_trips.remove(trip)
                if self._real_car:
                    LOGGER.debug("Alighted (time) : %s Car  %s  At  %s", trip.passenger_id, self._id, time)

    def _board(self, time: int) -> None:
        """Picks up the unboarded trips on this floor (FR-TIM-6 step 3, FR-CAR-8, FR-ASN-3, NFR-S1, NFR-S5).

        Passengers get on after riders get off. A passenger boards only if they go the car's way and a seat
        is free. The car's way is its riders' direction, or the first waiting passenger's when it is empty.
        A full car can still be given a trip (FR-ASN-5); that passenger waits for a seat.
        An express car never stops outside its served set.

        Args:
            time: the current time step, recorded as the pickup time.

        Raises:
            RuntimeError: if the car would stop at a floor outside its served set (NFR-S5), or would hold more
                riders than its capacity (NFR-S1).
        """
        waiting = self._unboarded_trips_at(self._current_floor)
        if not waiting:
            return
        if not self.can_serve_floor(self._current_floor):
            raise RuntimeError(f"car {self._id} would stop at floor {self._current_floor} "
                               "outside its served set (NFR-S5)")
        going = self._active_trips[0].direction if self._active_trips else waiting[0].direction
        seats_free = self._capacity - len(self._active_trips)
        for trip in [trip for trip in waiting if trip.direction == going][:seats_free]:
            trip.mark_pickup(time)
            self._unboarded_trips.remove(trip)
            self._active_trips.append(trip)
            # Log only real boardings, not the planning copies of the forward run.
            if self._real_car:
                LOGGER.debug("Boarded (time) : %s Car  %s  At  %s", trip.passenger_id, self._id, time)
        if len(self._active_trips) > self._capacity:
            raise RuntimeError(f"car {self._id} holds {len(self._active_trips)} riders, more than its capacity "
                               f"{self._capacity} (NFR-S1)")

    def copy(self) -> "Car":
        """An independent copy of this car, with copies of its trips (FR-ASN-4).

        Planning never changes the real car or trips. The copy does not count travel or log.

        Returns:
            a new car with the same state.
        """
        new_car = Car(self._id, self._current_floor, self._capacity, self._served_floors, self._parking_floor)
        new_car._real_car = False
        new_car._travel_direction = self._travel_direction
        new_car._active_trips = [trip.copy() for trip in self._active_trips]
        new_car._unboarded_trips = [trip.copy() for trip in self._unboarded_trips]
        return new_car

    def _unboarded_trips_at(self, floor: int) -> list[Trip]:
        """Unboarded trips whose passenger is on the given floor (FR-CAR-8).

        Args:
            floor: the floor to check.

        Returns:
            a new list of trips.
        """
        result = []
        for trip in self._unboarded_trips:
            if trip.source == floor:
                result.append(trip)
        return result

    @property
    def current_floor(self) -> int:
        """The current floor (FR-OUT-1: the position log shows each car's floor)."""
        return self._current_floor

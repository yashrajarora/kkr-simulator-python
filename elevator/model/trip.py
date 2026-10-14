"""One request as it is served, plus the times the simulation fills in."""

import copy as _copy

from elevator.model.direction import Direction
from elevator.model.passenger_request import PassengerRequest


class Trip:
    """One request as it is served: the passenger's details, plus the times the simulation fills in.

    Cars track trips during a run, and the summary reads the times at the end (FR-OUT-3).
    """

    def __init__(self, request: PassengerRequest):
        """Creates a trip from a request (FR-REQ-2).

        Args:
            request: the request this trip serves. The trip copies the values it needs.
        """
        self._passenger_id = request.passenger_id
        self._source = request.source
        self._destination = request.destination
        self._direction = request.direction
        self._request_time = request.request_time
        # Set later by the simulation. None until the passenger gets on or off.
        self._pickup_time: int | None = None
        self._drop_time: int | None = None

    def mark_pickup(self, time: int) -> None:
        """Records that the passenger got on the car (FR-TIM-6 step 4, pickup).

        Args:
            time: the time of pickup.
        """
        self._pickup_time = time

    def mark_drop(self, time: int) -> None:
        """Records that the passenger got off the car (FR-TIM-6 step 4, drop-off).

        Args:
            time: the time of drop-off.
        """
        self._drop_time = time

    @property
    def wait_time(self) -> int:
        """Wait time: time steps between the request and pickup (FR-OUT-3).

        Returns:
            pickup time minus the request time.
        """
        return self._pickup_time - self._request_time

    @property
    def total_time(self) -> int:
        """Total time: time steps between the request and drop-off (OBJ-2).

        Returns:
            drop-off time minus the request time.
        """
        return self._drop_time - self._request_time

    def copy(self) -> "Trip":
        """An independent copy of this trip, including its times (FR-ASN-4).

        Planning uses copies, so it never changes the real trip.

        Returns:
            a new trip with the same details and times.
        """
        return _copy.copy(self)

    @property
    def request_time(self) -> int:
        """Time step the request was made (FR-REQ-2)."""
        return self._request_time

    @property
    def passenger_id(self) -> str:
        """Passenger identifier, used in output and error messages (FR-REQ-2)."""
        return self._passenger_id

    @property
    def source(self) -> int:
        """Floor the passenger starts from (FR-REQ-1)."""
        return self._source

    @property
    def destination(self) -> int:
        """Floor the passenger wants to reach (FR-REQ-1)."""
        return self._destination

    @property
    def direction(self) -> Direction:
        """Direction of the trip (FR-REQ-2, FR-ASN-3). Passengers board only in this direction."""
        return self._direction

    @property
    def pickup_time(self) -> int | None:
        """Pickup time, or None if the passenger has not got on yet (FR-OUT-3, FR-ASN-4b)."""
        return self._pickup_time

    @property
    def drop_time(self) -> int | None:
        """Drop-off time, or None if the passenger has not got off yet (FR-TIM-6, NFR-S4)."""
        return self._drop_time

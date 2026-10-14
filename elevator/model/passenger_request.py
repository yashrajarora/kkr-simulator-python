"""One row of the request file: a passenger who asks for a ride (FR-REQ-1, FR-REQ-2)."""

from dataclasses import dataclass

from elevator.model.direction import Direction


@dataclass(frozen=True)
class PassengerRequest:
    """One row of the request file: a passenger who asks for a ride (FR-REQ-1, FR-REQ-2).

    Immutable, so nothing can change the destination after assignment (NFR-S3).

    Attributes:
        request_time: time step the request was made.
        passenger_id: passenger identifier.
        source: floor the passenger starts from.
        destination: floor the passenger wants to reach.
    """

    request_time: int
    passenger_id: str
    source: int
    destination: int

    @property
    def direction(self) -> Direction:
        """Direction of the trip, derived from source and destination (FR-REQ-2).

        Returns:
            UP if the destination is above the source, otherwise DOWN.
        """
        # The destination is above the source: the passenger goes UP. Otherwise DOWN.
        if self.destination > self.source:
            return Direction.UP
        return Direction.DOWN

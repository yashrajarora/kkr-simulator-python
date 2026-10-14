"""Results printed at the end of a run (FR-OUT-3)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Summary:
    """Results printed at the end of a run (FR-OUT-3).

    Attributes:
        wait_stats: statistics for wait times.
        total_stats: statistics for total times (wait plus travel, OBJ-2).
        p95_is_max: True when there are fewer than 20 passengers, so the 95th percentile equals the maximum.
        average_travel: average travel time, total minus wait, per passenger.
        floors_travelled: floors moved by each car, in car-number order.
        observations: notes on the time distributions and the system behaviour, one line each.
    """

    @dataclass(frozen=True)
    class Stats:
        """Statistics for one measure (wait or total), in time steps.

        Attributes:
            min: smallest value.
            max: largest value.
            average: mean value.
            p95: 95th percentile, nearest rank (FR-OUT-3).
            std_dev: population standard deviation (FR-OUT-3).
        """

        min: int
        max: int
        average: float
        p95: int
        std_dev: float

    wait_stats: Stats
    total_stats: Stats
    p95_is_max: bool
    average_travel: float
    floors_travelled: list[int]
    observations: list[str]

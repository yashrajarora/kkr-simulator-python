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
        total_ticks: the time step of the last drop-off, which is the length of the run.
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
            median: the middle value, the typical passenger (OBJ-2).
            p95: 95th percentile, nearest rank (FR-OUT-3, OBJ-5 for waits).
            std_dev: population standard deviation (FR-OUT-3).
        """

        min: int
        max: int
        average: float
        median: float
        p95: int
        std_dev: float

    wait_stats: Stats
    total_stats: Stats
    p95_is_max: bool
    average_travel: float
    total_ticks: int
    floors_travelled: list[int]
    observations: list[str]

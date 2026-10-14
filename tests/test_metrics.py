"""Tests the nearest-rank 95th percentile, the population standard deviation, and the under-20 note (FR-OUT-3)."""

import pytest

from elevator.metrics.metrics import Metrics
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


def trip(passenger_id: str, pickup: int, drop: int) -> Trip:
    """A trip requested at time 0 and picked up and dropped off at the given times.

    Args:
        passenger_id: the passenger identifier.
        pickup: the pickup time.
        drop: the drop-off time.

    Returns:
        the trip.
    """
    result = Trip(PassengerRequest(0, passenger_id, 1, 5))
    result.mark_pickup(pickup)
    result.mark_drop(drop)
    return result


def test_percentile_uses_nearest_rank():
    """FR-OUT-3: with 20 values, the 95th percentile is the value at position ceil(0.95 x 20) = 19."""
    values = list(range(1, 21))
    assert Metrics.percentile95(values) == 19


def test_percentile_equals_max_for_fewer_than_twenty_values():
    """FR-OUT-3: with fewer than 20 values, the 95th percentile equals the maximum."""
    assert Metrics.percentile95([3, 9, 1, 7, 5]) == 9


def test_std_dev_is_population_version():
    """FR-OUT-3: standard deviation is the population version (divide by n)."""
    assert Metrics.std_dev([2, 4, 4, 4, 5, 5, 7, 9], 5.0) == pytest.approx(2.0)


def test_observations_describe_median_longest_wait_and_last_drop_off():
    """Three passengers requested at time 0: waits 2, 3 and 11, drop-offs at 5, 6 and 14. The median wait is 3,
    the longest waiter is c with 11 steps, one passenger waited more than twice the median (c), and the last
    drop-off is at 14."""
    trips = [trip("a", 2, 5), trip("b", 3, 6), trip("c", 11, 14)]

    notes = Metrics.observations(trips)

    assert notes[0].startswith("Median wait 3.0")
    assert notes[1].startswith("Longest wait: c, 11 steps")
    assert notes[2] == "Passengers waiting more than twice the median wait: 1."
    assert notes[3] == "Last drop-off at time step 14."


def test_average_travel_is_total_minus_wait():
    """Travel time is total minus wait for each passenger. In the trips above it is 3 for each one, so the average
    travel time is 3, and the floors of the cars are passed through unchanged."""
    trips = [trip("a", 2, 5), trip("b", 3, 6), trip("c", 11, 14)]

    summary = Metrics.of(trips, [7, 4])

    assert summary.average_travel == pytest.approx(3.0)
    assert summary.floors_travelled == [7, 4]


def test_summary_flags_fewer_than_twenty_passengers():
    """FR-OUT-3: the summary says when the 95th percentile equals the maximum."""
    small = Metrics.of([], [])
    assert small.p95_is_max


def test_stats_include_median_of_even_and_odd_counts():
    """FR-OUT-3, OBJ-2: the median is the middle value, or the mean of the two middle values."""
    assert Metrics.stats([1, 2, 3, 10]).median == pytest.approx(2.5)
    assert Metrics.stats([1, 2, 10]).median == pytest.approx(2.0)


def test_summary_has_efficiency_and_fairness_headline_lines():
    """FR-OUT-3, OBJ-2, OBJ-5: the summary states the median total time and the 95th percentile wait."""
    import io
    from elevator.files.output_writer import OutputWriter

    trips = [trip("a", 0, 1), trip("b", 0, 4), trip("c", 2, 9)]
    summary = Metrics.of(trips, [5])
    text = io.StringIO()
    OutputWriter(text).write_summary(summary)

    lines = text.getvalue().splitlines()
    efficiency = [line for line in lines if line.startswith("Efficiency (OBJ-2): median total time")]
    fairness = [line for line in lines if line.startswith("Fairness (OBJ-5): 95th percentile wait")]
    assert efficiency == [f"Efficiency (OBJ-2): median total time {summary.total_stats.median:.1f} steps "
                          f"(average {summary.total_stats.average:.2f}, wait plus travel)"]
    assert fairness == [f"Fairness (OBJ-5): 95th percentile wait {summary.wait_stats.p95} steps "
                        f"(maximum {summary.wait_stats.max})"]


def test_summary_states_total_ticks_as_last_drop_off():
    """FR-OUT-3: the total ticks is the time step of the last drop-off."""
    import io
    from elevator.files.output_writer import OutputWriter

    trips = [trip("a", 0, 4), trip("b", 1, 11), trip("c", 2, 9)]
    summary = Metrics.of(trips, [3])
    assert summary.total_ticks == 11
    text = io.StringIO()
    OutputWriter(text).write_summary(summary)
    assert "Total ticks: 11 (time step of the last drop-off)" in text.getvalue()

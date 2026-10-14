"""Calculates the summary statistics for wait and total time (FR-OUT-3, OBJ-2), and notes on the results."""

import math

from elevator.metrics.summary import Summary
from elevator.model.trip import Trip


class Metrics:
    """Calculates the summary statistics for wait and total time (FR-OUT-3, OBJ-2)."""

    @staticmethod
    def of(trips: list[Trip], floors_travelled: list[int]) -> Summary:
        """Builds the summary for all trips in a finished run (FR-OUT-3).

        Args:
            trips: every trip in the run.
            floors_travelled: floors moved by each car, in car-number order.

        Returns:
            the summary for wait times and total times, the travel average, the floors, and the observations.
        """
        waits = [trip.wait_time for trip in trips]
        totals = [trip.total_time for trip in trips]
        # FR-OUT-3: with fewer than 20 passengers the 95th percentile equals the maximum.
        p95_is_max = len(trips) < 20
        # Travel time is total minus wait. Its average is the average total minus the average wait.
        average_travel = 0.0
        if trips:
            average_travel = Metrics.stats(totals).average - Metrics.stats(waits).average
        return Summary(Metrics.stats(waits), Metrics.stats(totals), p95_is_max, average_travel,
                       floors_travelled, Metrics.observations(trips))

    @staticmethod
    def observations(trips: list[Trip]) -> list[str]:
        """Notes on the time distributions and the system behaviour (FR-OUT-3).

        The notes are: the median (the typical passenger), the longest waiter, how many waited much
        longer than the median, and when the last passenger got off.

        Args:
            trips: every trip in the run.

        Returns:
            one line per note. Empty when there are no trips.
        """
        notes = []
        if not trips:
            return notes
        waits = [trip.wait_time for trip in trips]
        totals = [trip.total_time for trip in trips]

        # The median is the typical passenger: half of them are at or below it.
        median_wait = Metrics.median(waits)
        notes.append(f"Median wait {median_wait:.1f}, median total {Metrics.median(totals):.1f}: "
                     f"half of the passengers waited {median_wait:.1f} steps or less.")

        # The longest waiter, and how that compares with the median.
        longest = trips[0]
        for trip in trips:
            if trip.wait_time > longest.wait_time:
                longest = trip
        if median_wait > 0:
            notes.append(f"Longest wait: {longest.passenger_id}, {longest.wait_time} steps "
                         f"({longest.wait_time / median_wait:.1f} times the median wait).")
        else:
            notes.append(f"Longest wait: {longest.passenger_id}, {longest.wait_time} steps.")

        # Passengers who waited much longer than the typical one.
        much_longer = 0
        for wait in waits:
            if wait > 2 * median_wait:
                much_longer += 1
        notes.append(f"Passengers waiting more than twice the median wait: {much_longer}.")

        # When the run ended for the last passenger.
        last_drop_off = 0
        for trip in trips:
            if trip.drop_time > last_drop_off:
                last_drop_off = trip.drop_time
        notes.append(f"Last drop-off at time step {last_drop_off}.")
        return notes

    @staticmethod
    def stats(values: list[int]) -> Summary.Stats:
        """Min, max, average, median, 95th percentile, and standard deviation of a list of values.

        Args:
            values: the values (may be empty).

        Returns:
            the statistics. All zeros for an empty list.
        """
        if not values:
            return Summary.Stats(0, 0, 0.0, 0.0, 0, 0.0)
        average = sum(values) / len(values)
        return Summary.Stats(min(values), max(values), average, Metrics.median(values),
                             Metrics.percentile95(values), Metrics.std_dev(values, average))

    @staticmethod
    def median(values: list[int]) -> float:
        """Median of a list of values: the middle value, or the mean of the two middle values when the count is even.

        Args:
            values: the values (not empty).

        Returns:
            the median.
        """
        ordered = sorted(values)
        n = len(ordered)
        if n % 2 == 1:
            return float(ordered[n // 2])
        return (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0

    @staticmethod
    def percentile95(values: list[int]) -> int:
        """95th percentile by the nearest-rank method (FR-OUT-3).

        Sort the values and take the value at position ceil(0.95 x n), counting from 1. Integer math
        avoids rounding errors: ceil(95n / 100) = (95n + 99) // 100.

        Args:
            values: the values (not empty).

        Returns:
            the 95th percentile value.
        """
        ordered = sorted(values)
        n = len(ordered)
        rank = (95 * n + 99) // 100
        return ordered[rank - 1]

    @staticmethod
    def std_dev(values: list[int], mean: float) -> float:
        """Population standard deviation: divides by n, not n - 1 (FR-OUT-3).

        Args:
            values: the values (not empty).
            mean: the mean of the values.

        Returns:
            the standard deviation.
        """
        sum_squares = 0.0
        for value in values:
            sum_squares += (value - mean) ** 2
        return math.sqrt(sum_squares / len(values))

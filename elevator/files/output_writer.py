"""Prints the run's output: the position log and the summary (FR-OUT-1, FR-OUT-3, NFR-O1).

The writer takes text streams, so the simulator core never prints by itself (NFR-O2). Tests pass
an io.StringIO to capture the output.
"""

from typing import TextIO

from elevator.metrics.summary import Summary


class OutputWriter:
    """Prints the run's output: the position log and the summary (FR-OUT-1, FR-OUT-3, NFR-O1)."""

    def __init__(self, out: TextIO, position_log: TextIO | None = None):
        """Creates the writer.

        Args:
            out: where the summary goes, usually sys.stdout.
            position_log: where the position log goes, usually a file (FR-OUT-1). Defaults to out,
                so one stream gets both.
        """
        self._out = out
        self._position_log = position_log if position_log is not None else out
        # True once the position log's header row has been written.
        self._position_header_written = False

    def write_position(self, time: int, floors: list[int]) -> None:
        """Writes the floor of every car for one time as a comma-separated row (FR-OUT-1).

        The first call also writes the header row: "time,Car1,Car2,...". Each row looks like "5,7,4".

        Args:
            time: the time step.
            floors: the floor of each car, in car-number order.
        """
        if not self._position_header_written:
            header = "time" + "".join(f",Car{number}" for number in range(1, len(floors) + 1))
            print(header, file=self._position_log)
            self._position_header_written = True
        row = ",".join([str(time)] + [str(floor) for floor in floors])
        print(row, file=self._position_log)

    def write_summary(self, summary: Summary) -> None:
        """Prints the summary table (FR-OUT-3). Says so when the 95th percentile equals the maximum.

        Args:
            summary: the statistics for the run.
        """
        print("Summary (time steps)", file=self._out)
        self._print_stats("Wait time  : ", summary.wait_stats)
        self._print_stats("Total time : ", summary.total_stats)
        if summary.p95_is_max:
            print("Note: fewer than 20 passengers, so the 95th percentile equals the maximum.", file=self._out)
        print(f"Efficiency (OBJ-2): average total time {summary.total_stats.average:.2f} steps "
              "(wait plus travel)", file=self._out)
        print(f"Average travel time {summary.average_travel:.2f} steps", file=self._out)
        print("Floors travelled: " + self._floors_line(summary.floors_travelled), file=self._out)
        print("Observations", file=self._out)
        for note in summary.observations:
            print(note, file=self._out)

    def _print_stats(self, label: str, stats: Summary.Stats) -> None:
        """Prints one row of the summary table.

        Args:
            label: the row label.
            stats: the statistics for that row.
        """
        print(f"{label}  min {stats.min}  max {stats.max}  avg {stats.average:.2f}  "
              f"p95 {stats.p95}  std {stats.std_dev:.2f}", file=self._out)

    @staticmethod
    def _floors_line(floors: list[int]) -> str:
        """The floors line of the summary: each car's floors, then the total of all cars (FR-OUT-3).

        Args:
            floors: the floors moved by each car, in car-number order.

        Returns:
            text such as "car 1 = 24, car 2 = 18, all cars = 42".
        """
        text = ""
        total = 0
        for number, car_floors in enumerate(floors, start=1):
            text += f"car {number} = {car_floors}, "
            total += car_floors
        return text + f"all cars = {total}"

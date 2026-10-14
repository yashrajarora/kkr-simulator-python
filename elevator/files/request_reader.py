"""Reads the request file: one row per request, in the form time, passenger_id, source, dest (FR-IN-1).

Every row is checked before the run starts. A bad row stops the run with a message that names the
line, such as "line 7: destination 80 exceeds 50 floors" (FR-IN-2, NFR-I3). Blank lines are
skipped. A first row that starts with "time" is treated as a header.
"""

from typing import TextIO

from elevator.model.passenger_request import PassengerRequest


class RequestReader:
    """Reads and checks the request file (FR-IN-1, FR-IN-2, NFR-I3)."""

    @staticmethod
    def read(source: TextIO, floors: int) -> list[PassengerRequest]:
        """Reads and checks all requests from the text (FR-IN-1). The caller opens the file or resource.

        Args:
            source: the request text, one row per line.
            floors: number of floors N, used to check source and destination (FR-IN-2).

        Returns:
            the requests, in file order (which is time order, FR-TIM-5).

        Raises:
            ValueError: with a message naming the line, if any row is invalid (NFR-I3).
        """
        requests = []
        ids = set()
        previous_time = 0
        lines = source.read().splitlines()

        for index, raw_line in enumerate(lines):
            line_no = index + 1
            line = raw_line.strip()
            # Skip blank lines and the header row.
            if not line or line.startswith("time,") or line == "time":
                continue
            request = RequestReader._parse_row(line_no, line, floors)
            if request.request_time < previous_time:
                raise _error(line_no, f"time {request.request_time} is earlier than the row above "
                                      "(rows must be in time order)")
            # set.add returns False when the id is already present, so a repeat is caught here.
            if request.passenger_id in ids:
                raise _error(line_no, f"passenger id '{request.passenger_id}' is used more than once")
            ids.add(request.passenger_id)
            previous_time = request.request_time
            requests.append(request)
        return requests

    @staticmethod
    def _parse_row(line_no: int, line: str, floors: int) -> PassengerRequest:
        """Parses and checks one row (FR-IN-2).

        Args:
            line_no: the line number, used in error messages.
            line: the trimmed line.
            floors: number of floors N.

        Returns:
            the parsed request.

        Raises:
            ValueError: if the row is invalid.
        """
        fields = line.split(",")
        if len(fields) != 4:
            raise _error(line_no, f"expected 4 fields (time, passenger_id, source, dest) but found {len(fields)}")
        time = RequestReader._parse_int(line_no, "time", fields[0])
        passenger_id = fields[1].strip()
        if not passenger_id:
            raise _error(line_no, "passenger id is empty")
        source = RequestReader._parse_int(line_no, "source", fields[2])
        destination = RequestReader._parse_int(line_no, "destination", fields[3])

        if time < 0:
            raise _error(line_no, f"time {time} is negative")
        RequestReader._check_floor(line_no, "source", source, floors)
        RequestReader._check_floor(line_no, "destination", destination, floors)
        if source == destination:
            raise _error(line_no, f"source and destination are both floor {source}")
        return PassengerRequest(time, passenger_id, source, destination)

    @staticmethod
    def _parse_int(line_no: int, name: str, text: str) -> int:
        """Parses a whole number from a field.

        Args:
            line_no: the line number, used in error messages.
            name: the field name, used in error messages.
            text: the field text.

        Returns:
            the parsed integer.

        Raises:
            ValueError: if the text is not a whole number.
        """
        try:
            return int(text.strip())
        except ValueError:
            raise _error(line_no, f"{name} '{text.strip()}' is not a whole number") from None

    @staticmethod
    def _check_floor(line_no: int, name: str, floor: int, floors: int) -> None:
        """Checks that a floor is in 1..N (FR-IN-2).

        Args:
            line_no: the line number, used in error messages.
            name: "source" or "destination".
            floor: the floor to check.
            floors: number of floors N.

        Raises:
            ValueError: if the floor is outside 1..N.
        """
        if floor > floors:
            raise _error(line_no, f"{name} {floor} exceeds {floors} floors")
        if floor < 1:
            raise _error(line_no, f"{name} {floor} is below floor 1")


def _error(line_no: int, problem: str) -> ValueError:
    """Builds the error for a bad row.

    Args:
        line_no: the line number.
        problem: what is wrong.

    Returns:
        the exception to raise.
    """
    return ValueError(f"line {line_no}: {problem}")

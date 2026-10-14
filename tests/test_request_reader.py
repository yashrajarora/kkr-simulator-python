"""Tests the request file reader (FR-IN-1, FR-IN-2, NFR-I3)."""

import io

import pytest

from elevator.files.request_reader import RequestReader
from elevator.model.passenger_request import PassengerRequest


def read(*lines: str, floors: int = 50) -> list[PassengerRequest]:
    """Reads a request file made of the given lines.

    Args:
        *lines: the file lines.
        floors: number of floors N.

    Returns:
        the checked requests.
    """
    return RequestReader.read(io.StringIO("\n".join(lines)), floors)


def test_reads_valid_rows_and_skips_header_and_blank_lines():
    """FR-IN-1: the header row and blank lines are skipped; the rest are read in order."""
    requests = read("time, passengerId, source, dest", "", "0, passenger1, 1, 51", "10, passenger3, 20, 1",
                    floors=60)

    assert len(requests) == 2
    assert requests[0] == PassengerRequest(0, "passenger1", 1, 51)
    assert requests[1] == PassengerRequest(10, "passenger3", 20, 1)


def test_rejects_destination_above_top_floor():
    """FR-IN-2 / NFR-I3: a destination above the building is rejected, naming the line."""
    with pytest.raises(ValueError) as error:
        read("time, passengerId, source, dest", "0, a, 1, 20", "5, b, 2, 80")

    assert str(error.value) == "line 3: destination 80 exceeds 50 floors"


def test_rejects_source_equal_to_destination():
    """FR-IN-2: a request whose source equals its destination is rejected."""
    with pytest.raises(ValueError):
        read("0, a, 4, 4")


def test_rejects_rows_out_of_time_order():
    """FR-TIM-5: rows must be in time order."""
    with pytest.raises(ValueError):
        read("10, a, 1, 5", "3, b, 1, 6")

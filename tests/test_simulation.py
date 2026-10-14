"""Full-run tests (FR-TIM-6, FR-OUT-1, NFR-S4, NFR-TS4)."""

import io

from elevator.config.sim_config import CarSpec, SimConfig, Strategy, TrafficMode
from elevator.files.output_writer import OutputWriter
from elevator.model.passenger_request import PassengerRequest
from elevator.simulator.simulation import Simulation


def two_cars(strategy: Strategy) -> SimConfig:
    """Two regular cars, 60 floors, capacity 10: enough for the Appendix A requests.

    Args:
        strategy: the assignment algorithm.

    Returns:
        the settings.
    """
    regular = CarSpec(10, 1, 1, None)
    return SimConfig(60, [regular, regular], strategy, TrafficMode.NORMAL, None)


def run_output(config: SimConfig, requests: list[PassengerRequest]) -> str:
    """Runs a simulation and returns its output text.

    Args:
        config: the settings.
        requests: the requests.

    Returns:
        everything the run printed.
    """
    text = io.StringIO()
    Simulation(config, requests, OutputWriter(text)).run_simulation()
    return text.getvalue()


def test_appendix_a_requests_are_all_served():
    """Appendix A requests: every passenger is served, and the first two passengers wait 0 time steps."""
    requests = [
        PassengerRequest(0, "passenger1", 1, 51),
        PassengerRequest(0, "passenger2", 1, 37),
        PassengerRequest(10, "passenger3", 20, 1),
    ]

    trips = Simulation(two_cars(Strategy.ROUND_ROBIN), requests, OutputWriter(io.StringIO())).run_simulation()

    assert len(trips) == 3
    for trip in trips:
        assert trip.drop_time >= trip.request_time, f"{trip.passenger_id} must be dropped off (NFR-S4)"
    assert trips[0].wait_time == 0
    assert trips[1].wait_time == 0


def test_passenger_waits_on_full_car_until_seat_frees():
    """FR-ASN-5: when the car is full, the passenger is still assigned at once and waits on the car until a seat
    frees up. Everyone is still served (NFR-S4)."""
    one_seat = CarSpec(1, 1, 1, None)
    config = SimConfig(30, [one_seat, one_seat], Strategy.ROUND_ROBIN, TrafficMode.NORMAL, None)
    requests = [
        PassengerRequest(0, "a", 1, 10),
        PassengerRequest(0, "b", 1, 10),
        PassengerRequest(0, "c", 1, 10),
    ]

    trips = Simulation(config, requests, OutputWriter(io.StringIO())).run_simulation()

    assert len(trips) == 3
    for trip in trips:
        assert trip.drop_time >= trip.request_time, f"{trip.passenger_id} must be dropped off (NFR-S4)"


def test_later_request_does_not_change_earlier_output():
    """NFR-TS4 / FR-TIM-5: changing a request made at time t must not change any output before t."""
    changed_later = [
        PassengerRequest(0, "a", 1, 20),
        PassengerRequest(50, "b", 30, 40),
    ]
    changed_differently = [
        PassengerRequest(0, "a", 1, 20),
        PassengerRequest(50, "b", 5, 10),
    ]

    first = run_output(two_cars(Strategy.NEAREST_CAR_FORWARD_RUN), changed_later)
    second = run_output(two_cars(Strategy.NEAREST_CAR_FORWARD_RUN), changed_differently)

    # Compare the position rows before time 50. Cut both texts at the row for time 50.
    assert first[:first.index("\n50,")] == second[:second.index("\n50,")]

"""Runs the elevator simulation one time step at a time (FR-TIM-1 to FR-TIM-6).

Each time step runs these steps in order (FR-TIM-6, same as the Java version):
    1. Record the car floors at the start of the tick (FR-OUT-1).
    2. Release the requests made at this time, and assign cars to them (FR-TIM-5, FR-ASN-1).
    3. Each car, in car-number order, drops off its riders, picks up waiting passengers
       (FR-ASN-3), and moves one floor (FR-TIM-2). See Car.run_step.
"""

from elevator.config.car_builder import build_cars
from elevator.config.sim_config import SimConfig
from elevator.dispatch.dispatch_strategy import DispatchStrategy
from elevator.dispatch.trip_estimator import TripEstimator
from elevator.files.output_writer import OutputWriter
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip
from elevator.simulator.request_queue import RequestQueue


class Simulation:
    """Runs the elevator simulation one time step at a time (FR-TIM-1 to FR-TIM-6)."""

    def __init__(self, config: SimConfig, all_requests: list[PassengerRequest], out: OutputWriter):
        """Creates the run.

        Args:
            config: startup settings.
            all_requests: the requests to serve, in time order.
            out: where the output goes (NFR-O2).
        """
        self._config = config
        self._cars = build_cars(config)
        estimator = TripEstimator(config.floors)
        self._queue = RequestQueue(DispatchStrategy.create(config, estimator))
        # All requests, in time order (FR-IN-1).
        self._all_requests = all_requests
        # Index of the next request to release.
        self._next_request_index = 0
        # Every trip created so far, in assignment order.
        self._trips: list[Trip] = []
        self._out = out
        # Current time, starting at 0 (FR-TIM-1).
        self._time_now = 0

    def run_simulation(self) -> list[Trip]:
        """Runs time steps until every request has been served (FR-TIM-1, NFR-PF1).

        Returns:
            one copy per trip, with its times. The copies are independent, so changing them does not
            change the run.

        Raises:
            RuntimeError: if the run does not finish within the safety time_limit (NFR-S4).
        """
        # Safety time_limit, only to stop an endless loop. The worst case is one car serving one passenger
        # at a time: a trip up to the pickup floor, then a trip down to the drop-off floor.
        last_request_time = self._all_requests[-1].request_time if self._all_requests else 0
        time_limit = last_request_time + 2 * self._config.floors * len(self._all_requests)
        while not self._finished():
            if self._time_now > time_limit:
                raise RuntimeError(f"run did not finish by time {time_limit} (NFR-S4)")
            self.step()
            self._time_now += 1
        return [trip.copy() for trip in self._trips]

    @property
    def floors_travelled_per_car(self) -> list[int]:
        """The floors each car moved during the run, in car-number order (FR-OUT-3).

        Returns:
            one count per car.
        """
        return [car.floors_travelled for car in self._cars]

    def step(self) -> None:
        """Runs one time step (FR-TIM-6)."""
        self._print_positions()
        self._assign_new_requests()
        for car in self._cars:
            car.run_step(self._time_now)

    def _assign_new_requests(self) -> None:
        """Step 1 of a time step: gives the requests made at this time their cars (FR-TIM-5, FR-ASN-1)."""
        self._trips.extend(self._queue.assign_car(self._requests_made_at(self._time_now), self._cars))

    def _requests_made_at(self, time: int) -> list[PassengerRequest]:
        """The requests made at this time (FR-TIM-5). Later requests are not read (NFR-S6).

        Args:
            time: the current time step.

        Returns:
            the requests made at this time step, in request order.
        """
        made = []
        # The list is in time order, so the requests for this time are at the front of the unread part.
        while self._next_request_index < len(self._all_requests):
            request = self._all_requests[self._next_request_index]
            if request.request_time != time:
                break
            made.append(request)
            self._next_request_index += 1
        return made

    def _print_positions(self) -> None:
        """Writes the floor of every car for this time step (FR-OUT-1)."""
        floors = [car.current_floor for car in self._cars]
        self._out.write_position(self._time_now, floors)

    def _finished(self) -> bool:
        """Whether the run is over (FR-TIM-5, NFR-S4).

        Every request is assigned the moment it is released, so once all are released, each one has
        a trip. The run is over when every trip has been dropped off.

        Returns:
            True when every request has been released and every trip has been dropped off.
        """
        all_requests_processed = self._next_request_index == len(self._all_requests)
        all_trips_dropped_off = all(trip.drop_time is not None for trip in self._trips)

        return all_requests_processed and all_trips_dropped_off


"""Predicts what a car would do if it took a new request (FR-ASN-5, FR-ASN-4b, FR-ASN-4c).

A car is eligible if it serves both floors of the request. A single request is taken even by a
full car, and the passenger waits for a seat (FR-ASN-5).

The predictions come from a forward run: a copy of the car runs forward, time by time, with the
same rules as the real run. The real car and trips are never changed.
"""

from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


class TripEstimator:
    """Predicts what a car would do if it took a new request (FR-ASN-5, FR-ASN-4b, FR-ASN-4c)."""

    def __init__(self, floors: int):
        """Args:
            floors: number of floors N, used to bound the forward run.
        """
        self._floors = floors

    def predict_trips(self, car: Car, request: PassengerRequest) -> list[Trip]:
        """The predicted trips if the car took the new request (FR-ASN-5). Used by Cost Based.

        Args:
            car: the car to test (not changed).
            request: the new request. Its request time is the time of assignment (FR-TIM-6 step 1).

        Returns:
            the predicted trips, the new request last. An empty list if the car does not serve both floors.
        """
        if car.can_serve_request_floors(request):
            return self._forward_run(car, request, False)
        return []

    def predict_pickup_time(self, car: Car, request: PassengerRequest) -> int | None:
        """The time step at which the car would pick up the new passenger (FR-ASN-4b).

        Stops and turns count, because the forward run includes them.

        Args:
            car: the car to test (not changed).
            request: the new request. Its request time is the time of assignment.

        Returns:
            the pickup time step, or None if the car cannot take the request or the passenger
            does not board in time.
        """
        if car.can_serve_request_floors(request):
            trips = self._forward_run(car, request, True)
            # The new request is last in the list.
            return trips[-1].pickup_time
        return None

    def _forward_run(self, car: Car, request: PassengerRequest, stop_at_pickup: bool) -> list[Trip]:
        """Runs copies of the car and the trip forward (FR-ASN-5). The copies are thrown away afterwards.

        With stop_at_pickup False, the run goes on until the passenger is dropped off, and returns
        the trips, or an empty list if that does not happen in time. With stop_at_pickup True, the
        run stops as soon as the passenger boards, and returns the trips even if they have not
        boarded yet.

        Args:
            car: the car to test.
            request: the new request. Its request time is the time the run starts.
            stop_at_pickup: True to stop when the passenger boards, False to run until drop-off.

        Returns:
            the trips, the new request last.
        """
        # Work on copies only, so the real car and trips are not changed.
        car_copy = car.copy()
        car_copy.add_trip(Trip(request))
        trips = car_copy.all_trips
        limit = self._forward_run_limit(request.request_time, self._floors, len(trips))
        # Each loop is one time step, with the same order as the real run (FR-TIM-6).
        t = request.request_time
        while t < limit and not self._run_is_finished(trips, stop_at_pickup):
            car_copy.run_step(t)
            t += 1
        if stop_at_pickup or self._all_dropped(trips):
            return trips
        return []

    @staticmethod
    def _run_is_finished(trips: list[Trip], stop_at_pickup: bool) -> bool:
        """Whether the forward run can stop: the new request has boarded, or everyone has been dropped off.

        Args:
            trips: the trips of the run, the new request last.
            stop_at_pickup: True to stop when the last trip boards.

        Returns:
            True if the run can stop now.
        """
        if stop_at_pickup:
            return trips[-1].pickup_time is not None
        return TripEstimator._all_dropped(trips)

    @staticmethod
    def _forward_run_limit(time: int, floors: int, trip_count: int) -> int:
        """The last time step a forward run may use. It stops an endless loop.

        Each trip needs at most one trip up and one trip down the building, so the run should end
        well before this. One extra trip is added as a margin.

        Args:
            time: the time the forward run starts.
            floors: number of floors N.
            trip_count: the number of trips on the car, including the new one.

        Returns:
            the last time step the forward run may use.
        """
        return time + 2 * floors * (trip_count + 1)

    @staticmethod
    def _all_dropped(trips: list[Trip]) -> bool:
        """Whether every trip in the list has been dropped off.

        Args:
            trips: the trips to check.

        Returns:
            True if none is still waiting or riding.
        """
        for trip in trips:
            if trip.drop_time is None:
                return False
        return True

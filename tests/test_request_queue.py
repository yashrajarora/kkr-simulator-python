"""Tests that express cars are checked first for the requests they can serve (FR-CAR-3, FR-ASN-4, FR-ASN-6)."""

from elevator.dispatch.nearest_car_forward_run_strategy import NearestCarForwardRunStrategy
from elevator.dispatch.round_robin_strategy import RoundRobinStrategy
from elevator.dispatch.trip_estimator import TripEstimator
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip
from elevator.simulator.request_queue import RequestQueue

# Floors an express car serves in these tests: the lobby, and floors 45 to 50.
EXPRESS_FLOORS = {1, 45, 46, 47, 48, 49, 50}


def test_request_served_by_express_car_goes_to_express_car():
    """An express car at floor 45 serves floors 1 and 45 to 50. A regular car at floor 44 is nearer to a passenger
    at floor 46, but the express car serves that passenger, so the express car takes them."""
    regular = Car(1, 44, 10, None, None)
    express = Car(2, 45, 10, EXPRESS_FLOORS, 45)
    queue = RequestQueue(NearestCarForwardRunStrategy(TripEstimator(50)))

    assigned = queue.assign_car([PassengerRequest(0, "p", 46, 1)], [regular, express])

    assert assigned[0] in express.all_trips


def test_round_robin_groups_same_direction_requests_on_one_car():
    """Two passengers made at the same time, both going UP from floor 1, are grouped onto the first car in
    rotation (FR-ASN-4a). The second car gets nothing."""
    first = Car(1, 1, 10, None, None)
    second = Car(2, 1, 10, None, None)
    queue = RequestQueue(RoundRobinStrategy())

    assigned = queue.assign_car([PassengerRequest(0, "passenger1", 1, 51),
                                    PassengerRequest(0, "passenger2", 1, 37)], [first, second])

    assert all(trip in first.all_trips for trip in assigned)
    assert second.all_trips == []


def test_request_outside_express_floors_goes_to_regular_car():
    """A passenger from floor 20 to floor 30 is outside the express car's floors, so the regular car takes them
    even though the express car is nearer."""
    regular = Car(1, 25, 10, None, None)
    express = Car(2, 45, 10, EXPRESS_FLOORS, 45)
    queue = RequestQueue(NearestCarForwardRunStrategy(TripEstimator(50)))

    assigned = queue.assign_car([PassengerRequest(0, "p", 20, 30)], [regular, express])

    assert assigned[0] in regular.all_trips


def test_express_car_that_is_ready_comes_before_one_going_the_other_way():
    """Two express cars serve floors 45 to 50. The first is going UP with a rider, so it cannot take a passenger
    going DOWN now. The second is idle, so it takes them (express cars that are ready come first)."""
    busy = Car(2, 45, 10, EXPRESS_FLOORS, 45)
    busy.add_trip(Trip(PassengerRequest(0, "rider", 45, 50)))
    busy._board(0)
    idle = Car(3, 47, 10, EXPRESS_FLOORS, 45)
    queue = RequestQueue(NearestCarForwardRunStrategy(TripEstimator(50)))

    assigned = queue.assign_car([PassengerRequest(0, "p", 48, 46)], [busy, idle])

    assert assigned[0] in idle.all_trips


def test_express_car_that_must_turn_around_beats_ready_regular_car():
    """NFR-TS5 (FR-ASN-6, tier 2). The express car is going UP with a rider, so it must turn around to take a
    passenger going DOWN. A regular car at floor 47 is idle and nearer, but the express car serves both floors,
    so it still takes the passenger."""
    express = Car(2, 45, 10, EXPRESS_FLOORS, 45)
    express.add_trip(Trip(PassengerRequest(0, "rider", 45, 50)))
    express._board(0)
    regular = Car(1, 47, 10, None, None)
    queue = RequestQueue(NearestCarForwardRunStrategy(TripEstimator(50)))

    assigned = queue.assign_car([PassengerRequest(0, "p", 48, 46)], [regular, express])

    assert assigned[0] in express.all_trips

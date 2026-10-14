"""Tests the car movement and boarding rules (FR-ASN-3, FR-CAR-4, FR-CAR-8, NFR-S1, NFR-S5, NFR-TS1, NFR-TS3)."""

import pytest

from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


def regular_car() -> Car:
    """A regular car, capacity 10, starting on floor 1, not parked."""
    return Car(1, 1, 10, None, None)


def test_does_not_board_passenger_going_the_other_way():
    """FR-ASN-3: a car going UP must not pick up a passenger going DOWN, even when it passes that
    passenger's floor."""
    car = regular_car()
    up = Trip(PassengerRequest(0, "up", 1, 10))
    down = Trip(PassengerRequest(0, "down", 4, 2))
    car.add_trip(up)
    car.add_trip(down)

    car.run_step(0)  # at floor 1: the UP passenger boards
    assert up.pickup_time is not None, "UP passenger should board at floor 1"

    car.run_step(1)
    assert car.current_floor == 3, "car with an UP rider keeps going UP"
    car.run_step(2)  # now at floor 4, where the DOWN passenger waits
    car.run_step(3)  # it passes floor 4 without taking the DOWN passenger
    assert car.current_floor == 5
    assert down.pickup_time is None, "DOWN passenger must not board while the car is going UP"


def test_car_heads_to_parking_after_last_drop_off_then_becomes_idle():
    """FR-TRF-3: with a parking floor set, an empty car heads for it after its last drop-off, and is IDLE with
    no direction once it gets there."""
    car = Car(1, 5, 10, None, 1)
    car.add_trip(Trip(PassengerRequest(0, "a", 5, 3)))

    car.run_step(0)  # boards at floor 5, moves to 4
    car.run_step(1)  # floor 3
    car.run_step(2)  # drop-off at floor 3, then heads for parking

    assert car.current_floor == 2

    car.run_step(3)  # reaches parking floor 1

    assert car.current_floor == 1
    assert car.floors_travelled == 4, "trip 5 to 3, then 3 to 1 for parking"

    car.run_step(4)  # idle at the parking floor: no more movement

    assert car.current_floor == 1
    assert car.floors_travelled == 4


def test_car_becomes_idle_after_last_drop_off():
    """FR-ASN-3: when the last rider gets off, the car becomes IDLE and drops the finished trip."""
    car = regular_car()
    trip = Trip(PassengerRequest(0, "a", 1, 3))
    car.add_trip(trip)

    car.run_step(0)  # boards at floor 1
    car.run_step(1)  # floor 2
    car.run_step(2)  # floor 3: drop-off

    assert car.current_floor == 3
    assert trip.drop_time == 2
    assert car.active_trips == [], "a finished trip is removed from the car"

    car.run_step(3)
    assert car.current_floor == 3, "with no parking floor, an empty car stays where it stopped"


def test_idle_car_boards_waiting_passenger_and_takes_their_direction():
    """FR-CAR-8: an IDLE car that has a waiting passenger on its floor boards them at once and takes their direction."""
    car = Car(1, 5, 10, None, None)
    trip = Trip(PassengerRequest(0, "a", 5, 2))
    car.add_trip(trip)

    car.run_step(0)

    assert trip.wait_time == 0
    assert car.current_floor == 4, "the car boarded its DOWN passenger and moved DOWN"


def test_express_car_passes_unserved_floors():
    """FR-CAR-4 / NFR-S5: an express car passes floors outside its served set without stopping."""
    express = Car(2, 1, 10, {1, 10}, 1)
    trip = Trip(PassengerRequest(0, "a", 1, 10))
    express.add_trip(trip)

    for t in range(10):
        express.run_step(t)
    assert trip.drop_time == 9, "express car takes one time per floor and stops only at 1 and 10"
    assert express.current_floor == 9, "once empty, the express car heads back toward its parking floor 1"


def test_express_car_rejects_stop_outside_served_set():
    """NFR-S5: an express car must never pick up a passenger on a floor outside its served set."""
    express = Car(2, 5, 10, {1, 10}, 1)
    express.add_trip(Trip(PassengerRequest(0, "a", 5, 10)))

    with pytest.raises(RuntimeError):
        express.run_step(0)


def test_full_car_leaves_waiting_passenger_behind():
    """NFR-S1: a full car takes nobody more. The passenger who cannot board stays waiting."""
    car = Car(1, 1, 1, None, None)
    first = Trip(PassengerRequest(0, "a", 1, 5))
    second = Trip(PassengerRequest(0, "b", 1, 6))
    car.add_trip(first)
    car.add_trip(second)

    car.run_step(0)

    assert first.wait_time == 0
    assert second.pickup_time is None, "second passenger must not board a full car"
    assert len(car.all_trips) == 2, "the second passenger is still on the car, waiting"


def test_empty_car_keeps_direction_while_a_unboarded_passenger_is_ahead():
    """FR-CAR-8: an empty car with unboarded passengers keeps its direction until none is ahead. A passenger
    added above the car does not turn it around while an unboarded passenger is still below."""
    car = Car(1, 4, 2, None, None)
    car.add_trip(Trip(PassengerRequest(0, "below", 2, 1)))
    car.add_trip(Trip(PassengerRequest(0, "above", 5, 7)))

    car.run_step(0)

    assert car.current_floor == 3, "the car keeps going DOWN toward the unboarded passenger below"


def test_empty_car_takes_direction_of_first_waiting_passenger_not_its_heading():
    """An empty car at floor 1 has two passengers waiting at floor 5: first one going DOWN, then one going UP.
    The car reaches floor 5 at the end of time 3 moving UP. At time 4 it boards the first passenger it takes,
    who is going DOWN, and the UP passenger waits (FR-CAR-8, FR-ASN-3, NFR-S2)."""
    car = regular_car()
    down = Trip(PassengerRequest(0, "down", 5, 2))
    up = Trip(PassengerRequest(0, "up", 5, 9))
    car.add_trip(down)
    car.add_trip(up)

    # Each tick: alight and board at the current floor, then move (FR-TIM-6).
    for t in range(5):
        car.run_step(t)

    assert down.pickup_time == 4
    assert up.pickup_time is None


def test_forward_run_copy_does_not_count_as_travel():
    """FR-OUT-3: only real travel counts. A forward-run copy moves its own floors, but the real car's count
    does not change, and the copy starts from zero."""
    car = regular_car()
    car.add_trip(Trip(PassengerRequest(0, "p", 1, 5)))
    car._board(0)
    car._move_one_floor()
    assert car.floors_travelled == 1

    copy = car.copy()
    copy._move_one_floor()
    copy._move_one_floor()

    assert car.floors_travelled == 1
    assert copy.floors_travelled == 0


def test_express_car_passes_floors_outside_its_served_set():
    """FR-CAR-4, NFR-TS3: an express car serving floors 1 and 10 passes floors 2 to 9 without stopping, so the
    rider goes straight from floor 1 to floor 10 and gets off at time 9."""
    express = Car(2, 1, 4, {1, 10}, 1)
    rider = Trip(PassengerRequest(0, "rider", 1, 10))
    express.add_trip(rider)
    express._board(0)

    # Each tick: alight and board at the current floor, then move (FR-TIM-6).
    time = 0
    while rider.drop_time is None:
        express._alight(time)
        express._board(time)
        express._move_one_floor()
        time += 1

    assert rider.drop_time == 9

"""Tests the simplified Nearest Car (floor distance, comparison only)."""

from elevator.dispatch.nearest_car_simple_strategy import NearestCarSimpleStrategy
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


def test_full_car_is_not_chosen_while_another_car_can_take_the_passenger():
    """A car with no room cannot take the passenger now, so the empty car far away takes them, even though the
    full car is nearer (FR-ASN-3)."""
    near_full = Car(1, 5, 1, None, None)
    near_full.add_trip(Trip(PassengerRequest(0, "existing", 5, 9)))

    far = Car(2, 20, 10, None, None)
    newcomer = PassengerRequest(0, "new", 6, 8)

    strategy = NearestCarSimpleStrategy()
    assert strategy.choose_best_car_by_strategy(newcomer, [near_full, far]) is far


def test_picks_nearest_by_floors():
    """The nearest car by floor distance wins."""
    near = Car(1, 4, 10, None, None)
    far = Car(2, 15, 10, None, None)
    request = PassengerRequest(0, "p", 5, 9)

    strategy = NearestCarSimpleStrategy()
    assert strategy.choose_best_car_by_strategy(request, [near, far]) is near


def test_car_going_the_other_way_is_not_ready_so_another_car_is_chosen():
    """A car going UP with a rider cannot take a passenger going DOWN now, even though it is nearer. The empty car
    far away can take them now, so it is chosen (FR-ASN-3)."""
    near_up = Car(1, 5, 10, None, None)
    rider = Trip(PassengerRequest(0, "rider", 5, 20))
    near_up.add_trip(rider)
    near_up._board(0)  # the rider on floor 5 boards, and the car becomes UP

    far = Car(2, 20, 10, None, None)
    down = PassengerRequest(0, "down", 7, 2)

    strategy = NearestCarSimpleStrategy()
    assert strategy.choose_best_car_by_strategy(down, [near_up, far]) is far

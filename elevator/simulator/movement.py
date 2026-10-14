"""How a car chooses its direction and moves one floor in a time step (FR-CAR-2, FR-CAR-8, FR-TRF-3 to FR-TRF-5).

The rules here only read the values they are given and return results. They hold no state. Car works
out its targets, calls these rules, and applies the result, so the real car and the forward-run copies
always follow the same rules.

The direction policy is LOOK: keep going in the current direction while there is a target ahead, reverse
when there is not, and stop when there are no targets. Targets are the passengers' floors, and the
parking floor for an empty car.
"""

from elevator.model.direction import Direction


def unboarded_trip_direction(current: Direction, unboarded_floors_above: bool, unboarded_floors_below: bool) -> Direction:
    """The next direction for an unboarded trip (FR-CAR-8).

    Args:
        current: the direction the car is travelling in now.
        unboarded_floors_above: whether an unboarded passenger is at this floor or above it.
        unboarded_floors_below: whether an unboarded passenger is at this floor or below it.

    Returns:
        the current direction if a target is ahead in it, otherwise the other direction if a target is
        that way, otherwise IDLE (no targets at all).
    """
    if current == Direction.UP and unboarded_floors_above:
        return Direction.UP
    if current == Direction.DOWN and unboarded_floors_below:
        return Direction.DOWN
    if unboarded_floors_above:
        return Direction.UP
    if unboarded_floors_below:
        return Direction.DOWN
    return Direction.IDLE


def is_ahead(floor: int, direction: Direction, passenger_floor: int) -> bool:
    """Whether a passenger's floor is at this floor or beyond it in the given direction (FR-CAR-8).

    Args:
        floor: the car's floor.
        direction: the direction to look in. UP looks up; anything else looks down.
        passenger_floor: the floor the passenger starts from.

    Returns:
        True if the passenger is at or ahead of the car in that direction.
    """
    if direction == Direction.UP:
        return passenger_floor >= floor
    return passenger_floor <= floor


def heading_for_new_trip(floor: int, passenger_floor: int) -> Direction:
    """The direction a car takes toward its first new passenger (FR-CAR-8).

    Args:
        floor: the car's floor.
        passenger_floor: the floor the new passenger starts from.

    Returns:
        UP if the passenger is at or above the car, otherwise DOWN.
    """
    if passenger_floor >= floor:
        return Direction.UP
    return Direction.DOWN


def parking_direction(floor: int, parking_target: int) -> Direction:
    """The direction of the move toward the parking floor (FR-TRF-3 to FR-TRF-5).

    Args:
        floor: the car's floor.
        parking_target: the parking floor.

    Returns:
        UP or DOWN while the car is moving to the parking floor, IDLE when it is there.
    """
    if parking_target > floor:
        return Direction.UP
    if parking_target < floor:
        return Direction.DOWN
    return Direction.IDLE


def step_toward(floor: int, direction: Direction) -> int:
    """The floor one step from this floor in the given direction.

    Args:
        floor: the current floor.
        direction: UP adds one floor; anything else subtracts one.

    Returns:
        the new floor.
    """
    if direction == Direction.UP:
        return floor + 1
    return floor - 1

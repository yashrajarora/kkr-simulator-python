"""Takes the requests made at one time step and assigns each to a car at once (FR-ASN-1, FR-ASN-5).

It never sees a later request, so it cannot look ahead (FR-TIM-5, NFR-S6). A request becomes a
trip when the car takes it.
"""

from elevator.dispatch.dispatch_strategy import DispatchStrategy
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest
from elevator.model.trip import Trip


class RequestQueue:
    """Gives each request made at one time step its car (FR-ASN-1, FR-ASN-5)."""

    def __init__(self, strategy: DispatchStrategy):
        """Args:
            strategy: the assignment algorithm, chosen once at startup (FR-ASN-4).
        """
        self._strategy = strategy

    @staticmethod
    def _filter_eligible_cars(request: PassengerRequest, cars: list[Car]) -> list[Car]:
        """The cars the strategy may choose from for one request, in three tiers (FR-ASN-6).

        1. Express cars that serve both floors and can take the passenger now.
        2. Express cars that serve both floors, even if they must turn around first.
        3. Every car.

        The first tier that has a car is used.

        Args:
            request: the request.
            cars: all cars, in car-number order.

        Returns:
            the cars from the first tier that has any.
        """
        ready_express_cars = []
        express_cars = []
        for car in cars:
            if car.is_express and car.can_serve_request_floors(request):
                express_cars.append(car)
                if car.can_honor_elevator_constraints(request.source, request.direction):
                    ready_express_cars.append(car)
        if ready_express_cars:
            return ready_express_cars
        if express_cars:
            return express_cars
        return cars

    def assign_car(self, requests_now: list[PassengerRequest], cars: list[Car]) -> list[Trip]:
        """Gives each request made at this time a car (FR-ASN-1, FR-ASN-5, NFR-S3).

        A request that gets a car becomes a trip, assigned once only. The trips are returned,
        not printed.

        Args:
            requests_now: the requests made at this time step, in request order. Their request
                time is the time of assignment.
            cars: all cars, in car-number order.

        Returns:
            each new trip, in assignment order.
        """
        # Work on a copy, because assigned requests are removed from the waiting list.
        waiting = list(requests_now)
        trips = []

        # Loop until every request is assigned.
        while waiting:
            first = waiting[0]
            car = self._strategy.choose_best_car_by_strategy(first, self._filter_eligible_cars(first, cars))
            # Only Round Robin groups several requests onto one car. For the other strategies this
            # returns just the first request.  The group will have only one request in case of non-round-robin strategy
            group = self._strategy.group_for(car, first, waiting)
            # Give the car each request of the group as a trip.
            for request in group:
                trip = Trip(request)
                car.add_trip(trip)
                waiting.remove(request)
                trips.append(trip)
        return trips

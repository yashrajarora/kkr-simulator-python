"""The interface every assignment algorithm implements (FR-ASN-1, FR-ASN-4, NFR-D1).

One class per algorithm, so a new algorithm needs no change to the simulator.

An implementation must not change any car or trip. It only reads state and uses TripEstimator
to test cars.
"""

from abc import ABC, abstractmethod

from elevator.config.sim_config import SimConfig, Strategy
from elevator.dispatch.trip_estimator import TripEstimator
from elevator.model.car import Car
from elevator.model.passenger_request import PassengerRequest


class DispatchStrategy(ABC):
    """Chooses the car for a new trip (FR-ASN-1, FR-ASN-4)."""

    @abstractmethod
    def choose_best_car_by_strategy(self, request: PassengerRequest, cars: list[Car]) -> Car | None:
        """Returns the car that should serve the trip (FR-ASN-5: only an eligible car may be chosen).

        Args:
            request: the new request. Its request time is the time of assignment.
            cars: all cars, in car-number order.

        Returns:
            the chosen car, or None if no car is eligible right now. The simulator then keeps the
            trip unboarded and tries again on the next time (FR-ASN-5).
        """

    def group_for(self, car: Car, request: PassengerRequest,
                  unassigned_requests: list[PassengerRequest]) -> list[PassengerRequest]:
        """The requests that go to the car together with this one (FR-ASN-4a).

        By default, just the request. A strategy that groups requests overrides this.

        Args:
            car: the car chosen for the request.
            request: the request chosen first.
            unassigned_requests: the requests made at this time that are not yet assigned.

        Returns:
            the group, with the request first.
        """
        return [request]

    @staticmethod
    def create(config: SimConfig, estimator: TripEstimator) -> "DispatchStrategy":
        """Creates the strategy chosen in the settings, used for the whole run (FR-ASN-4).

        Args:
            config: the settings. The strategy name is read from here.
            estimator: checks each car and predicts its trips.

        Returns:
            the strategy object.
        """
        # Imported here, not at the top, because the strategy modules import this module.
        # A top-level import would be circular.
        from elevator.dispatch.balanced_strategy import BalancedStrategy
        from elevator.dispatch.cost_based_strategy import CostBasedStrategy
        from elevator.dispatch.nearest_car_simple_strategy import NearestCarSimpleStrategy
        from elevator.dispatch.nearest_car_forward_run_strategy import NearestCarForwardRunStrategy
        from elevator.dispatch.nearest_car_strategy import NearestCarStrategy
        from elevator.dispatch.round_robin_strategy import RoundRobinStrategy

        match config.strategy:
            case Strategy.ROUND_ROBIN:
                return RoundRobinStrategy()
            case Strategy.NEAREST_CAR:
                return NearestCarStrategy()
            case Strategy.NEAREST_CAR_FORWARD_RUN:
                return NearestCarForwardRunStrategy(estimator)
            case Strategy.NEAREST_CAR_SIMPLE:
                return NearestCarSimpleStrategy()
            case Strategy.COST_BASED:
                return CostBasedStrategy(estimator)
            case Strategy.BALANCED_STRATEGY:
                return BalancedStrategy(estimator)

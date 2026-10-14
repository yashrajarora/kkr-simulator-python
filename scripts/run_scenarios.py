"""Runs every strategy on generated traffic scenarios, and saves the averages to docs/scenario_results.json.

    python scripts/run_scenarios.py

Each scenario builds its request files from fixed seeds, so the same run always gives the same numbers. The
results are averages over the seeds. Nothing in config/, data/ or out/ is changed.

Only the standard library is used, and the simulator is called directly, not through the settings file.
"""

import io
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

import sys

# Lets the script import the elevator package when it is run from any folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elevator.config.config_loader import ConfigLoader
from elevator.config.sim_config import Strategy
from elevator.dispatch.dispatch_strategy import DispatchStrategy
from elevator.files.output_writer import OutputWriter
from elevator.files.request_reader import RequestReader
from elevator.metrics.metrics import Metrics
from elevator.simulator.simulation import Simulation

RESULTS_FILE = Path(__file__).resolve().parent.parent / "docs" / "scenario_results.json"

# Parking floors used by the downward rush (FR-TRF-4), one per car.
DOWN_RUSH_PARKING = {"parkingFloor.1": "10", "parkingFloor.2": "6", "parkingFloor.3": "3"}


def morning_rush_requests(seed: int, passengers: int = 30) -> str:
    """Most passengers leave the lobby (floor 1) and go up."""
    rnd = random.Random(seed)
    rows, t = [], 0
    for i in range(passengers):
        t += rnd.choice([0, 1, 1, 2])
        src = 1 if rnd.random() < 0.8 else rnd.randint(2, 10)
        if src == 1:
            dst = rnd.randint(2, 10)
        else:
            dst = rnd.randint(src + 1, 10) if src < 10 else 9
        rows.append(f"{t}, p{i + 1:02d}, {src}, {dst}")
    return _csv(rows)


def evening_rush_requests(seed: int, passengers: int = 30) -> str:
    """Most passengers go down to the lobby (floor 1)."""
    rnd = random.Random(seed)
    rows, t = [], 0
    for i in range(passengers):
        t += rnd.choice([0, 1, 1, 2])
        dst = 1 if rnd.random() < 0.8 else rnd.randint(2, 9)
        if dst == 1:
            src = rnd.randint(2, 10)
        else:
            src = rnd.randint(dst + 1, 10) if dst < 10 else 10
        rows.append(f"{t}, p{i + 1:02d}, {src}, {dst}")
    return _csv(rows)


def uniform_requests(seed: int, passengers: int, floors: int, max_gap: int) -> str:
    """Random origin and destination on any floors, with random gaps between requests."""
    rnd = random.Random(seed)
    rows, t = [], 0
    for i in range(passengers):
        t += rnd.randint(0, max_gap)
        src, dst = rnd.sample(range(1, floors + 1), 2)
        rows.append(f"{t}, p{i + 1:02d}, {src}, {dst}")
    return _csv(rows)


def _csv(rows: list[str]) -> str:
    return "time, id, source, dest\n" + "\n".join(rows) + "\n"


# Each scenario: the traffic mode, the building, the request generator and the number of seeds.
SCENARIOS = {
    "morning rush": dict(mode="MORNING_RUSH", floors=10, cars=3, capacity=4, seeds=100,
                         requests=morning_rush_requests, extra={}),
    "evening rush": dict(mode="EVENING_RUSH", floors=10, cars=3, capacity=4, seeds=100,
                         requests=evening_rush_requests, extra=DOWN_RUSH_PARKING),
    "uniform traffic": dict(mode="NORMAL", floors=10, cars=3, capacity=4, seeds=20,
                            requests=lambda s: uniform_requests(s, 30, 10, 2), extra={}),
    "sparse traffic": dict(mode="NORMAL", floors=10, cars=3, capacity=4, seeds=20,
                           requests=lambda s: uniform_requests(s, 10, 10, 6), extra={}),
    "large building": dict(mode="NORMAL", floors=50, cars=6, capacity=8, seeds=20,
                           requests=lambda s: uniform_requests(s, 100, 50, 2), extra={}),
}


def jain_index(values: list[int]) -> float:
    """Jain's fairness index: 1 when every value is equal, 1/n when one value holds everything."""
    total = sum(values)
    if total == 0:
        return 1.0
    return total * total / (len(values) * sum(v * v for v in values))


# Counts the passengers each car is given. The simulator creates its strategy with DispatchStrategy.create,
# so this wraps that strategy and records the car chosen for each request.
_chosen: dict[str, list[int]] = {}
_original_create = DispatchStrategy.create


class _RecordingStrategy(DispatchStrategy):
    def __init__(self, inner: DispatchStrategy, name: str):
        self._inner = inner
        self._name = name

    def choose_best_car_by_strategy(self, request, cars):
        car = self._inner.choose_best_car_by_strategy(request, cars)
        if car is not None:
            _chosen.setdefault(self._name, []).append(cars.index(car))
        return car

    def group_for(self, car, request, unassigned_requests):
        return self._inner.group_for(car, request, unassigned_requests)


def _create_recording(config, estimator):
    return _RecordingStrategy(_original_create(config, estimator), config.strategy.name)


def run_one(scenario: dict, seed: int, strategy: Strategy) -> dict:
    """Runs one strategy on one generated request file, and returns its measures for that run."""
    props = {
        "requests": "generated.csv",
        "strategy": strategy.name,
        "mode": scenario["mode"],
        "floors": str(scenario["floors"]),
        "cars": str(scenario["cars"]),
        "capacity": str(scenario["capacity"]),
        **scenario["extra"],
    }
    config = ConfigLoader.build(props)
    requests = RequestReader.read(io.StringIO(scenario["requests"](seed)), config.floors)
    _chosen.clear()
    DispatchStrategy.create = staticmethod(_create_recording)
    try:
        simulation = Simulation(config, requests, OutputWriter(io.StringIO()))
        trips = simulation.run_simulation()
    finally:
        DispatchStrategy.create = staticmethod(_original_create)
    summary = Metrics.of(trips, simulation.floors_travelled_per_car)
    per_car = [_chosen.get(strategy.name, []).count(car) for car in range(scenario["cars"])]
    return {
        "avg_wait": summary.wait_stats.average,
        "max_wait": summary.wait_stats.max,
        "avg_total": summary.total_stats.average,
        "median_total": summary.total_stats.median,
        "p95_wait": summary.wait_stats.p95,
        "total_ticks": summary.total_ticks,
        "floors": sum(summary.floors_travelled),
        "balance": jain_index(per_car),
    }


def main() -> None:
    results = {}
    for name, scenario in SCENARIOS.items():
        per_strategy = defaultdict(lambda: defaultdict(list))
        for seed in range(scenario["seeds"]):
            for strategy in Strategy:
                for measure, value in run_one(scenario, seed, strategy).items():
                    per_strategy[strategy.name][measure].append(value)
        results[name] = {
            "seeds": scenario["seeds"],
            "strategies": {
                strategy: {
                    measure: {
                        "mean": statistics.mean(values),
                        "se": statistics.stdev(values) / math.sqrt(len(values)),
                    }
                    for measure, values in measures.items()
                }
                for strategy, measures in per_strategy.items()
            },
        }
        print(f"{name}: done ({scenario['seeds']} seeds)")
    RESULTS_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Results written to: {RESULTS_FILE}")


if __name__ == "__main__":
    main()

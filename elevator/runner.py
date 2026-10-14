"""Runs the simulation for the settings: one strategy, or every strategy in turn (FR-ASN-4, FR-OUT-1 to FR-OUT-3).

The settings are read from elevator.properties, in the elevator/resources folder, and so are the request
files. Output files go to the folder the program runs from. See ConfigLoader for the keys.
"""

from pathlib import Path
from typing import TextIO

from elevator.config.config_loader import ConfigLoader
from elevator.config.sim_config import SimConfig, Strategy
from elevator.files.output_writer import OutputWriter
from elevator.files.request_reader import RequestReader
from elevator.metrics.metrics import Metrics
from elevator.model.passenger_request import PassengerRequest
from elevator.simulator.simulation import Simulation

# Name of the settings file (NFR-U1).
SETTINGS_FILE = "elevator.properties"

# Position log for one strategy, as comma-separated rows, in the folder the program runs from (FR-OUT-1).
POSITION_FILE = "positions.csv"

# Summary file, in the folder the program runs from (FR-OUT-3).
SUMMARY_FILE = "summary.txt"

# The settings value that runs every strategy in turn.
ALL_STRATEGIES = "ALL"

# Folder holding the settings file and the request files, next to this module.
RESOURCES_DIR = Path(__file__).resolve().parent / "resources"

# Folder for the output files, in the project root (created when a run starts).
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "out"


def read_settings() -> dict[str, str]:
    """Reads the settings file from the resources folder (NFR-U1).

    Returns:
        the settings, as written in the file.

    Raises:
        RuntimeError: if the settings file is not in the resources folder.
    """
    path = RESOURCES_DIR / SETTINGS_FILE
    if not path.is_file():
        raise RuntimeError(f"settings file {SETTINGS_FILE} not found in the resources folder")
    with open(path, encoding="utf-8") as settings_file:
        return ConfigLoader.read_properties(settings_file)


def run_elevator(settings: dict[str, str]) -> None:
    """Runs the simulation for the settings: every strategy for ALL, otherwise the one named (FR-OUT-1 to FR-OUT-3).

    Args:
        settings: the settings read from the file.

    Raises:
        OSError: if a file cannot be read or written.
        ValueError: if a setting or request is not valid.
        RuntimeError: if a run fails.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)
    if settings.get("strategy", "").strip().upper() == ALL_STRATEGIES:
        _run_all_strategies(settings)
    else:
        with open(OUTPUT_DIR / SUMMARY_FILE, "w", encoding="utf-8") as summary_writer:
            _run_and_record(ConfigLoader.build(settings), OUTPUT_DIR / POSITION_FILE, summary_writer)
        print(f"Summary written to: {(OUTPUT_DIR / SUMMARY_FILE).resolve()}")


def _run_all_strategies(settings: dict[str, str]) -> None:
    """Runs every strategy, one after another, with the same settings and requests (FR-ASN-4).

    Each run writes its position log to its own file, and all the summaries go to one file.

    Args:
        settings: the settings, with strategy=ALL.

    Raises:
        OSError: if a file cannot be read or written.
    """
    with open(OUTPUT_DIR / SUMMARY_FILE, "w", encoding="utf-8") as summary:
        for strategy in Strategy:
            # Copy the settings, then change only the strategy for this run.
            one_strategy = dict(settings)
            one_strategy["strategy"] = strategy.name
            _run_and_record(ConfigLoader.build(one_strategy), OUTPUT_DIR / f"positions_{strategy.name}.csv", summary)
    print(f"Summaries of all strategies written to: {(OUTPUT_DIR / SUMMARY_FILE).resolve()}")


def _run_and_record(config: SimConfig, position_file: str, summary_writer: TextIO) -> None:
    """Runs one simulation. Writes its position log to the given file, and its summary to the summary
    stream under a heading that names the strategy (FR-OUT-1, FR-OUT-3).

    Args:
        config: the settings for this run.
        position_file: the file for the position log.
        summary_writer: the stream the summary is written to.

    Raises:
        OSError: if a file cannot be read or written.
    """
    all_requests = _load_passenger_requests(config)
    with open(position_file, "w", encoding="utf-8") as positions_writer:
        out = OutputWriter(positions_writer)

        simulation = Simulation(config, all_requests, out)
        trips = simulation.run_simulation()

        print(f"Strategy: {config.strategy.name}", file=summary_writer)
        OutputWriter(summary_writer).write_summary(Metrics.of(trips, simulation.floors_travelled_per_car))
        print(file=summary_writer)
    print(f"Position log written to: {Path(position_file).resolve()}")


def _load_passenger_requests(config: SimConfig) -> list[PassengerRequest]:
    """Reads the request file named in the settings, from the resources folder (FR-IN-1).

    Args:
        config: the settings, which name the request file.

    Returns:
        the checked requests.

    Raises:
        RuntimeError: if the request file is not in the resources folder.
        OSError: if the file cannot be read.
    """
    path = RESOURCES_DIR / config.requests_file
    if not path.is_file():
        raise RuntimeError(f"request file {config.requests_file} not found in the resources folder")
    with open(path, encoding="utf-8") as request_file:
        return RequestReader.read(request_file, config.floors)

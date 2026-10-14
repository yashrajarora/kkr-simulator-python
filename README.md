# Elevator Scheduling Simulation

## 1. PURPOSE AND SCOPE

Design an intelligent, modern elevator simulation for a high-rise building. It uses destination dispatch: a passenger enters both origin and destination before boarding, and the system immediately tells them which car to take.

The simulation is discrete-time and shows how real-time passenger requests are handled efficiently across multiple cars, with a focus on managing requests and optimizing elevator operations.


## How to run your code

Requirements:

- Python 3.10 or later (the code uses `match` statements and `X | None` type hints).
- Standard library only to run the simulator.
- `pytest` to run the tests (see `requirements-dev.txt`).

Settings are read from `config/elevator.properties`. The request files are in the `data/` folder, and the name in `requests=` is relative to it.
Run the simulator from the project folder:

    python main.py

Outputs, written to the `out/` folder in the project (created on each run):

- `positions.csv`, or `positions_<STRATEGY>.csv` when `strategy=ALL`.
- `summary.txt`.

To run the tests:

    python -m pip install -r requirements-dev.txt
    python -m pytest

## How long I spent on the project

32 hours

## Assumptions, simplifications and trade-offs

- **Requests:** the request file must be in time order, with unique passenger ids. Two requests may share a time.
- **Eligibility:** a car is eligible only if it serves both the source and the destination. Capacity does not
  stop an assignment. A full car can still be given a trip, and the passenger waits for a seat.
- **Express cars:** they never stop outside their served set, and floor 1 is always in it.
- **Tick order:** each tick runs alight, then board, then move, for each car in car-number order. A car that
  has a waiting passenger on its floor boards them before it moves.
- **Movement:** a car with riders moves in their direction. A car with unboarded passengers keeps its direction
  while a passenger is ahead, then reverses. An empty car goes to its parking floor, and
  stays where it stopped in NORMAL mode.
- **No boarding or alighting time:** passengers board and alight in the same tick the car is at their floor.
- **Strategies:**
  - `NEAREST_CAR` first keeps only the cars with room for the passenger now (or all eligible cars if none has
    room). Then it measures distance in floors, plus the detour when a car is heading away. It is an
    estimate and does not count stops or seats.
  - `NEAREST_CAR_FORWARD_RUN` runs a copy of each car forward, so it is exact for these rules, but it is slower.
  - `NEAREST_CAR_SIMPLE` measures floors only, as a comparison baseline.
  - `COST_BASED` and `BALANCED_STRATEGY` also use forward runs, so their cost grows with the number of cars and trips.
  - `BALANCED_STRATEGY` weights pickup time and load equally (both 1.0), set in the code.
- **Summary:** two headline lines give efficiency as the median total time (OBJ-2) and fairness as the 95th
  percentile wait (OBJ-5). With fewer than 20 passengers, the 95th percentile equals the maximum, and the
  summary says so.
- **Safety limit:** a run that does not finish within a computed number of ticks stops with an error, rather
  than looping forever.

## What I'd improve with more time

- **Add zoning**: split the building into zones, so each car serves only its zone and trips that cross zones are handled. Zoning is out of scope for this version, because regular cars serve all floors.
- **Intelligent handling of the peak modes** (morning, lunch and evening). Instead of sending every idle car to a single parking floor, spread the idle cars over a group of floors: near the lobby in the morning, and across the upper floors in the evening. Send each car to the group of floors most likely to need it next, and batch passengers at the lobby so that a car leaves full.
- **Configurable boarding and alighting time.** Although not specified in the functional requirements, make the number of ticks taken to board and alight a setting. The requirements currently treat this time as out of scope, so every passenger boards and alights in the tick the car is at their floor.
- **Energy-saving strategy.** Add a strategy that picks cars to reduce the floors travelled (the energy used), for example by giving a request to a car that is already moving toward it, and by grouping passengers so that fewer trips are needed. Compare its energy use, measured in floors travelled, with the other strategies.
- **Test scenarios.** Build a more comprehensive test suite: cover the main flows end to end, every strategy and traffic mode, and corner cases that there was not time to test, such as simultaneous requests at the same floor, a full car at its capacity limit, and requests at the top and bottom floors.
- **Live requests.** Accept requests while the simulation runs, through a REST interface, instead of only from a file read at the start. The request source would sit behind the interface the requirements describe, so the simulator core would not change. Live requests would need the same time-order checks as the file input.

## Layout

    main.py              entry point: argument check, logging and exit codes
    elevator/
      runner.py          reads settings, runs one strategy or all of them, writes outputs
      config/            settings, their checks and building the cars
      model/             Car, Trip, PassengerRequest, Direction
      dispatch/          assignment strategies and eligibility rules
      files/             request reader and output writer
      metrics/           statistics and summary
      simulator/         tick loop, request queue and movement rules
    config/              settings file (elevator.properties)
    data/                request files
    out/                 run output (created on each run)
    tests/               pytest tests
    docs/                requirements

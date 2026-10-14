---
name: elevator-sim
description: Work on the kkr-simulator-py elevator dispatch simulator. Use for changes to dispatch strategies (Round Robin, Nearest Car, Cost Based, Balanced), the tick loop, settings, outputs, tests, requirements, or the summary slides, or when asked how to run or test the simulator.
---

# Elevator simulator

## Run and test
- Run: `python -m elevator.main` from the project root, with no arguments. Settings: `elevator/resources/elevator.properties`. Request files are in the same folder.
- Test: `python -m pytest` (config in `pytest.ini`, tests in `tests/`).
- Runs write to `out/`, and each run overwrites the previous files. `strategy=ALL` writes one set per strategy.

## Layout
- `elevator/config/`: settings and car setup
- `elevator/model/`: Car, Trip, PassengerRequest, Direction
- `elevator/dispatch/`: strategies and the trip estimator (forward run)
- `elevator/simulator/`: tick loop, request queue, movement and boarding
- `elevator/files/`: request reader and output writer
- `elevator/metrics/`: statistics
- `docs/requirements.md`: the contract. FR-* and NFR-* IDs appear in code comments and tests.
- `docs/strategies.ipynb`: strategy write-up with results. Its numbers can lag behind the code, so check them before quoting.
- `docs/elevator_strategies_summary.pptx`: summary slides.

## Rules
- Read `docs/requirements.md` before changing behaviour. If the behaviour should change, change the requirement first.
- Each tick runs: record car floors, release requests, assign, alight then board, move one floor. The real run and the forward-run copies use the same order.
- A forward run works on copies and must never change the real car or trips.
- A strategy is one class implementing `DispatchStrategy` (NFR-D1). Adding one must not change the simulator core.
- The simulator core does not print. Output goes through the writer (NFR-O2).
- Results must be reproducible (NFR-T1). Add randomness only with a seed.
- NFR-U1 and NFR-E3 forbid command-line arguments. Changing that means changing those requirements first.
- Balanced strategy weights are in `balanced_strategy.py`, not in the settings file (yet). Check the file for the current values.

## Git
- Do not commit, push or discard changes unless the user asks.
- Do not commit `.idea/` or `docs/~$*.pptx` (Office lock file).
- Check `git status` first. The working tree may contain the user's uncommitted work.

## Before finishing a change
- Run `python -m pytest`.
- If results change, state the strategy and sample file, and give the before and after numbers.
- Check that the README, `docs/requirements.md`, the notebook and the slides still match the code.

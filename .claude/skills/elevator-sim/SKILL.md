---
name: elevator-sim
description: Work on the kkr-simulator-py elevator dispatch simulator. Use for changes to dispatch strategies (Round Robin, Nearest Car, Nearest Car Forward Run, Nearest Car Simple, Cost Based, Balanced), the tick loop, settings, outputs, tests, requirements, efficiency and fairness measures, scenario results, the notebook, or the summary slides, or when asked how to run or test the simulator.
---

# Elevator simulator

## Run and test
- Run: `python main.py` from the project root, with no arguments. Settings: `config/elevator.properties`. Request files are in `data/`.
- Test: `python -m pytest` (config in `pytest.ini`, tests in `tests/`).
- Runs write to `out/`, and each run overwrites the previous files. `strategy=ALL` writes one set per strategy.
- Scenario results: `python scripts/run_scenarios.py` from any folder (about 10 seconds). It rewrites `docs/scenario_results.json`, which holds the mean and standard error over generated files for each scenario and strategy. It saves no per-run values.

## Layout
- `elevator/config/`: settings and car setup
- `elevator/model/`: Car, Trip, PassengerRequest, Direction
- `elevator/dispatch/`: strategies and the trip estimator (forward run)
- `elevator/simulator/`: tick loop, request queue, movement and boarding
- `elevator/files/`: request reader and output writer
- `elevator/metrics/`: statistics and the summary
- `scripts/run_scenarios.py`: generated traffic scenarios, writes `docs/scenario_results.json`
- `docs/requirements.md`: the contract. FR-*, NFR-* and OBJ-* IDs appear in code comments and tests.
- `docs/strategies.ipynb`: strategy write-up with results. Its numbers can lag behind the code, so check them before quoting.
- `docs/elevator_strategies_summary.pptx`: summary slides. Slides 26 to 30 are per-scenario appendix tables taken from `docs/scenario_results.json`.

## Data
- `data/requests_big.csv`: 100 passengers, 50 floors, 6 cars, capacity 10. This is the standard comparison input, and it matches the building in `config/elevator.properties`.
- `data/sample_best_*.csv`: 12-passenger inputs, each made so one strategy is best on one measure. They show that each strategy can win somewhere. They don't show overall ranking.
- Compare fairness only on inputs with at least 20 passengers. With fewer, the 95th percentile equals the maximum.

## Measures
- Efficiency (OBJ-2): median total time, where total time = wait + travel. Average total time is also reported.
- Fairness (OBJ-5): 95th percentile wait (nearest rank). Max wait is also reported.
- The summary shows these as two headline lines after the table (FR-OUT-3).

## Rules
- Read `docs/requirements.md` before changing behaviour. If the behaviour should change, change the requirement first.
- Each tick runs: record car floors, release requests, assign, alight then board, move one floor. The real run and the forward-run copies use the same order.
- A forward run works on copies and must never change the real car or trips.
- A strategy is one class implementing `DispatchStrategy` (NFR-D1). Adding one must not change the simulator core.
- The simulator core does not print. Output goes through the writer (NFR-O2).
- Results must be reproducible (NFR-T1). Add randomness only with a seed.
- NFR-U1 and NFR-E3 forbid command-line arguments. Changing that means changing those requirements first.
- Balanced strategy weights are in `balanced_strategy.py`, not in the settings file (yet). Check the file for the current values.
- NEAREST_CAR filters on room only: it measures floor distance over eligible cars with room now, or over all eligible cars if none has room. FR-ASN-5 says ready cars are preferred, and FR-ASN-4b-E is the stated exception.

## Changing a strategy: documents to update
1. `docs/requirements.md` first.
2. Re-run the tests and `python main.py` on the chosen input.
3. Re-run `python scripts/run_scenarios.py`.
4. Notebook (`docs/strategies.ipynb`): edit the markdown and re-run the code cells (sections 5 to 8). `nbconvert` is not installed. Run the code cells in a Python session and store the stdout and figures as outputs. The file uses CRLF line endings, so keep them when writing it back.
5. Slides: check slides 11, 15, 17 to 24 and 26 to 30 against the new numbers. Slide 18 and 19 use `requests_big.csv`. Slides 21 to 23 use `docs/scenario_results.json`. Rush hour is the average of morning and evening rush.
6. README.

## Git
- Do not commit, push or discard changes unless the user asks.
- Do not commit `.idea/`, `.pytest_cache/` or `docs/~$*.pptx` (Office lock file).
- Check `git status` first. The working tree may contain the user's uncommitted work, such as `config/elevator.properties` and `.gitignore`.

## Files that may be locked
- If saving the `.pptx` fails with "Permission denied", the deck is probably open in PowerPoint. Ask the user to close it, then retry. Check the file still opens before and after.

## Before finishing a change
- Run `python -m pytest`.
- If results change, state the strategy and sample file, and give the before and after numbers.
- Check that the README, `docs/requirements.md`, the notebook and the slides still match the code.

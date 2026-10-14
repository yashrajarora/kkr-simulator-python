# Elevator Destination-Dispatch Simulator - Requirements
**Status: Draft**


## 1. PURPOSE AND SCOPE

Design an intelligent, modern elevator simulation for a high-rise building. It uses destination dispatch: a passenger enters both origin and destination before boarding, and the system immediately tells them which car to take.

The simulation is discrete-time and shows how real-time passenger requests are handled efficiently across multiple cars, with a focus on managing requests and optimizing elevator operations.


## 2. OBJECTIVES

- OBJ-1 No starvation: every request is served. No passenger waits indefinitely to be picked up or dropped off.
- OBJ-2 Efficiency: minimize total time per passenger, where total_time = wait_time + travel_time.
- OBJ-3 Capacity: no car exceeds its capacity.
- OBJ-4 Direction: no wrong-way riding is possible.


## 3. OUT OF SCOPE

- Time taken for a passenger to board or alight. (Meaning the door open and close etc.)
- Maintenance and emergency stops.
- Persistence beyond the output files.
- REST input for requests (future; see NFR-I1 and NFR-I2).
- Whether floor 1 (lobby) is in an express car's served set. It always is (FR-CAR-7); making this configurable is out of scope.
- Zoned buildings, where some trips cross zones and no single car serves them. Regular cars serve all floors (FR-CAR-6), so this does not arise.


## 4. GLOSSARY

- Floor: a numbered level, 1 to N, where N is the configured floor count. Floor 1 is the lobby.
- Car: one elevator. Each car has a direction of UP, DOWN, or IDLE (FR-CAR-2).
- Unboarded passenger: a passenger assigned to a car who has not boarded it yet.
- Regular car: a car that serves all floors.
- Express car: a car that serves only its configured set of floors (its served set). It does not stop anywhere else.
- Served set: the floors an express car is allowed to stop at, fixed at startup. Always includes floor 1.
- Rider: a passenger currently inside a car.
- Passenger: a person identified by a request, from request time until drop-off.
- Request: a passenger's tick time, id, source, and destination.
- Tick: one discrete time step. One tick is one floor of car travel.
- Eligible car: a car that can serve a request. It must serve both the source and the destination. Room and direction do not decide eligibility: the request is assigned at once, and the passenger boards when the car is going their way and has a free seat (FR-ASN-3, NFR-S1).


## 5. FUNCTIONAL REQUIREMENTS

### 5.1 Floors
- FR-FLR-1 The number of floors shall be read at simulator startup.
- FR-FLR-2 Every floor shall be served by at least one car, regular or express.

### 5.2 Cars
- FR-CAR-1 The number of cars and each car's capacity shall be read at simulator startup.
- FR-CAR-2 Each car shall have a direction: UP, DOWN, or IDLE. Its direction is the riders' direction while it has riders. Otherwise it is the direction it is moving toward its next unboarded passenger or its parking floor. IDLE means the car is not moving: it is empty and at its parking floor (or stays where it stopped if it has none).
- FR-CAR-9 Each car's starting floor shall be set at startup. The default is floor 1.
- FR-CAR-3 Startup configuration may designate zero or more cars as express. Each express car has a served set. Cars not designated express are regular cars.
- FR-CAR-4 An express car shall not stop at, board from, or alight at any floor outside its served set. Express cars move at the same speed as regular cars, one tick per floor. Their only advantage is that they do not stop at, or detour to, floors outside their served set.
- FR-CAR-5 The served set of each express car is fixed for the whole run.
- FR-CAR-6 At least one regular car shall exist, so that every trip has at least one possible car. Regular cars serve all floors.
- FR-CAR-7 Every express car's served set shall include floor 1.
- FR-CAR-8 Movement rules. (a) A car with riders moves in their direction. All riders share one direction, and the car keeps it until its last drop-off. (b) A car with no riders but with unboarded passengers keeps its direction while an unboarded passenger is at or ahead of it in that direction, and reverses otherwise. When an empty car is given its first unboarded passenger, its direction is set toward that passenger. (c) A car with no riders and no unboarded passengers moves to its parking floor, or stays if it has none, and is IDLE once it is there. (d) A car with no riders that reaches a floor with a waiting passenger boards the passengers going in the direction of the first waiting passenger, before it moves.

### 5.3 Requests
- FR-REQ-1 A passenger shall specify a source and a destination in the request.
- FR-REQ-2 Each request shall contain: time step, passenger id, source, and destination. Its direction is derived from source and destination.
- FR-REQ-3 A request, once made, shall not be cancelled.
- FR-REQ-4 Each request shall be served by exactly one car.

### 5.4 Assignment
- FR-ASN-1 The simulator shall assign each passenger to a specific car.
- FR-ASN-2 Once assigned, the destination shall not change.
- FR-ASN-3 Direction rule. A passenger shall board only when the car is about to travel in the passenger's direction. A car that passes a waiting passenger's floor while going the other way, or while carrying riders going the other way, shall not board that passenger. All riders in a car shall share one direction. A car shall turn around only after its last drop-off in the current direction.
- FR-ASN-4 The assignment algorithm shall be chosen at startup and used for the whole run. Options:
  - FR-ASN-4a Round Robin. Assign each passenger to the next eligible car in rotation.
  - FR-ASN-4b Nearest Car, forward run (NEAREST_CAR_FORWARD_RUN). Evaluate all eligible cars and assign the passenger to the nearest one. Distance is measured in ticks: the number of ticks until the car reaches the source floor moving in the passenger's direction, including any stops it must make first. Every tick of movement counts, including movement away from the source floor, such as a car that goes down 2 floors and then back up to serve a passenger, which is 5 ticks. Distance is never measured in floors. The distance is found by running a copy of the car forward (the forward run), so stops, seats and turns are all counted.
  - FR-ASN-4b-E Nearest Car, floor estimate (NEAREST_CAR). Like FR-ASN-4b-S, it prefers cars that can take the passenger now. Its distance is the number of floors to the source, plus the floors to the car's turn point and back when the car is heading away from the source. This is an estimate: it does not count stops, seats or time spent at a floor, so it does not meet FR-ASN-4b.
  - FR-ASN-4b-S Nearest Car, simplified (comparison only). Same as FR-ASN-4b, but distance is the number of floors from the car to the source, and a car that can take the passenger now is preferred. This does not meet FR-ASN-4b. It is kept only to compare its results with FR-ASN-4b.
  - FR-ASN-4c Cost Based. Keep waits balanced across passengers. Minimize the maximum wait and total time, so no passenger is left far behind to improve the average. Measured by max, 95th percentile, and standard deviation of wait and total time. Each eligible car is scored as follows:
    - For each eligible car, predict the wait of the new passenger and of every passenger the car would pick up after this assignment. The longest of these waits is the car's score.
    - Choose the car where the longest wait of any passenger on it is shortest. Ties go to the lower car number.
  - FR-ASN-4d Balanced (BALANCED_STRATEGY). Trades off how soon a car can pick the passenger up against how many passengers it already carries. Each eligible car is scored as wait_time_weight x wait + car_load_weight x passengers. The wait is the number of ticks from the request until the car picks the passenger up (from the forward run). The passengers are the riders plus the unboarded passengers. The car with the lowest score is chosen, and ties go to the lower car number. Both weights default to 1.0. They are set in the code for now, not in the settings file.
- FR-ASN-5 A request shall be assigned immediately, at the time it is made, to an eligible car. A car that can take the passenger now is preferred. If no car can, the passenger may wait on the car for a seat or for the car to turn around.
- FR-ASN-6 Express first. Among eligible cars, express cars that serve both the source and the destination are considered before regular cars. If any such express car can take the passenger now (FR-ASN-3), only those cars are considered. Otherwise, all such express cars are considered, even if one must turn around first. A regular car is considered only when no express car serves both floors. This rule takes precedence over FR-ASN-4a, FR-ASN-4b, FR-ASN-4b-S, and FR-ASN-4c: the assignment algorithm chooses only from the cars this rule allows, so it may not pick the nearest or lowest-cost car when that car is outside the allowed set.

### 5.5 Time
- FR-TIM-1 The simulation shall run in discrete time steps.
- FR-TIM-2 One time unit equals one floor of car travel, up or down. This applies to every car, express or regular.
- FR-TIM-3 Requests shall use the same time steps as the simulation.
- FR-TIM-4 The simulation shall advance one time unit at a time, even if input requests skip ahead.
- FR-TIM-5 The simulation shall not look ahead in the request list. Requests are read in time order and released only when the current tick reaches their time. No decision at a tick, including assignment, cost comparison, and statistics, may use a request stamped with a later time.
- FR-TIM-6 Each tick shall run these steps in this order. Steps 3 and 4 run for each car in car-number order:
  1. Admit requests stamped with this tick.
  2. Assign them, using car positions from the start of the tick.
  3. Alight riders whose destination is the current floor, then board waiting passengers going in the car's direction, at the car's current floor.
  4. Move each car one floor.
  5. Record the position log and metrics.
  A passenger requested at tick t who boards at t has a wait of 0. A car may pick up passengers and then leave the floor in the same tick.

### 5.6 Traffic modes
- FR-TRF-1 The simulator shall accept one traffic mode at startup: NORMAL, MORNING_RUSH, LUNCH_OUT_RUSH, LUNCH_BACK_RUSH, or EVENING_RUSH. Default: NORMAL.
- FR-TRF-2 The traffic mode shall be fixed for the whole run.
- FR-TRF-3 In MORNING_RUSH and LUNCH_BACK_RUSH (people arriving and going up), the parking floor of every car is floor 1. A car with no assigned passengers shall move to its parking floor and stay there until it is assigned a passenger. After serving its passengers, it returns to its parking floor.
- FR-TRF-4 In LUNCH_OUT_RUSH and EVENING_RUSH (people leaving and going down), each car has a fixed parking floor set at startup (NFR-C3). A car with no assigned passengers shall move to its parking floor and stay there until it is assigned a passenger. After serving its passengers, it returns to its parking floor.
- FR-TRF-5 In NORMAL mode, a car with no assigned passengers stays where it last stopped.

### 5.7 Input
- FR-IN-1 Requests shall be read from a file. Format: `time, id, source, dest`, one request per row. Example in Appendix A.
- FR-IN-2 A request whose source equals its destination, or whose source or destination is outside floors 1 to N, shall be rejected during input validation and shall not be served. The run does not start (NFR-I3).

### 5.8 Output
- FR-OUT-1 Position log. For every time step from 0, the simulator shall log the location of every car, one comma-separated row per time step, with a header row. Format in Appendix B. The file is positions.csv for one strategy. When all strategies run (ALL), there is one file per strategy, named positions_<STRATEGY>.csv.
- FR-OUT-3 Summary. On completion, the simulator shall write the minimum, maximum, average, 95th percentile, and standard deviation of wait time and total time to the file summary.txt. When all strategies run (ALL), the summary has one section per strategy, headed by the strategy name.
  - The 95th percentile uses the nearest-rank method: sort the values, and take the value at position ceil(0.95 × n), counting from 1.
  - When there are fewer than 20 passengers, the 95th percentile equals the maximum, and the summary shall say so.


## 6. NON-FUNCTIONAL REQUIREMENTS

Each NFR is listed with the functional section it relates to.

### 6.1 Running the program
- NFR-E1 [NFR-U1] The simulator is run with `python main.py` and no arguments. It is run from the project folder.
- NFR-E2 [NFR-U1] The simulator uses only the Python standard library. Running the tests needs `pytest`, listed in `requirements-dev.txt`.
- NFR-E3 [NFR-U2] Exit codes: 0 on success, 1 for an error (a missing file, a bad setting, or a failed run), and 2 for a usage error (any argument given).
- NFR-E4 [FR-OUT-1, FR-OUT-3] The run writes its output files to the `out` folder in the project, creates that folder if needed, and prints where the files are. With one strategy these are `positions.csv` and `summary.txt`. With `ALL` they are one `positions_<STRATEGY>.csv` per strategy and one `summary.txt`.
- NFR-E5 [FR-OUT-1] The Boarded and Alighted messages go to stderr, not to the output files.

### 6.2 Configurability
- NFR-C1 [5.1] The floor count is a startup parameter and is not hardcoded.
- NFR-C2 [5.2] Car count, per-car capacity, and per-car starting floor (FR-CAR-9) are startup parameters. Changing them requires only an edit to the settings file, not a code change. Startup validation rejects a starting floor outside 1 to N, and rejects an express car's starting floor that is outside its served set.
- NFR-C3 [5.6] Each car's parking floor is a startup parameter, used in LUNCH_OUT_RUSH and EVENING_RUSH, where every car must set its own parking floor. Startup validation rejects a run in those modes if any car's parking floor is missing, rejects a parking floor outside 1 to N, and rejects an express car's parking floor that is outside its served set.
- NFR-C4 [5.2] The number of express cars and each express car's served set are startup parameters. Startup validation rejects a served set that is empty, does not include floor 1, or contains floors outside 1 to N.

### 6.3 Correctness and safety
Enforced as runtime assertions in the simulator, not only by tests. A violation fails the run.
- NFR-S1 [5.2, OBJ-3] No car holds more riders than its capacity at any tick.
- NFR-S2 [FR-ASN-3, OBJ-4] Every rider's direction matches the car's direction at every tick.
- NFR-S3 [FR-REQ-4, FR-ASN-2] Each request is assigned to exactly one car, and its destination never changes after assignment.
- NFR-S4 [FR-OUT-3, OBJ-1] When the run ends, every request must be served. If any request is unserved, the run reports a failure instead of partial statistics.
- NFR-S5 [FR-CAR-4] An express car never stops at, boards at, or alights at a floor outside its served set.
- NFR-S6 [FR-TIM-5] No request is assigned at a tick earlier than its request time. A request is admitted only at its own tick.

### 6.4 Strategy design
- NFR-D1 [FR-ASN-4] Each strategy is one class implementing a common interface. Adding a strategy requires no changes to the simulator core.
- NFR-D2 [FR-ASN-4c] One assignment decision stays bounded as cars and floors increase, so Cost Based (which evaluates every eligible car) stays practical. Target: one decision in under 1 ms at the reference scale in NFR-PF1.

### 6.5 Determinism
- NFR-T1 [5.5] The same config and request file always produce identical logs and metrics. Required for comparing the Java and Python versions.
- NFR-T2 [5.5] Any randomness, such as generated traffic in a future version, comes from a seed passed at startup.
- NFR-T3 [5.5] The simulation runs on one thread.

### 6.6 Performance
- NFR-PF1 [5.5] Reference scale: 50 floors, 6 cars (1 express, with the lobby always in its served set), and 3,000 passengers per run. A run ends when all passengers are served. Target: a run at this scale completes in a few seconds on a laptop.

### 6.7 Input
- NFR-I1 [5.7] Requests are read from a file in this version. REST event input is future work.
- NFR-I2 [5.7] The request source sits behind an interface, so a REST source can be added later without changing the core.
- NFR-I3 [5.7] Invalid input (see FR-IN-2) produces an error naming the line and the problem, such as "line 7: destination 80 exceeds 50 floors". The run does not start.

### 6.8 Output
- NFR-O1 [5.8] The position log covers every time step, in the format in Appendix B.
- NFR-O2 [5.8] The simulator core has no console dependency. Output goes through a writer interface so tests can capture it.
- NFR-O3 [5.8] A run leaves no persistent state beyond the output files.

### 6.9 Usability
- NFR-U1 [5.7] One command runs a simulation with no command-line arguments. All settings are read from a settings file (`elevator.properties` in the `config` folder of the project root: `elevator-core/src/main/resources` in the Java version, `config/` in the Python version). The request file it names is read from the `data` folder. Strategy, traffic mode, and request file are the only required settings; everything else has a default.
- NFR-U2 [5.7] Errors print a short message, not a stack trace. Passing any argument prints a short usage message.

### 6.10 Testability
- NFR-TS1 [FR-ASN-3] Each direction rule in FR-ASN-3 has at least one test that fails if the rule is broken.
- NFR-TS2 [FR-ASN-4] Each strategy can be tested in isolation with a fixed scenario.
- NFR-TS4 [FR-TIM-5] Changing the content of a request stamped at tick t does not change any output before tick t. This test catches any look-ahead in the request list.
- NFR-TS3 [FR-CAR-4, FR-ASN-5] Tests cover express skipping: an express car passes floors outside its served set, and a request outside the served set is never assigned to it.
- NFR-TS5 [FR-ASN-6] Tests cover express first: a request is given to a ready express car over a ready regular car, and to a regular car only when no express car serves both floors.

## Appendix A - Sample Request File

```csv
time, id, source, dest
0, passenger1, 1, 51
0, passenger2, 1, 37
10, passenger3, 20, 1
```


## Appendix B - Sample Output

Position log (FR-OUT-1), file positions.csv, one row per time step, with a header row:
```csv
time,Car1,Car2,Car3
0,10,4,6
1,9,4,5
```


Summary (FR-OUT-3): minimum, maximum, average, 95th percentile, and standard deviation of wait and total time.

## Relevant Files

- `state.py` - To be modified to hold the new state required for the planner (plans, maps, fingerprints).
- `agents/uuid_planner.py` - The location for the new core planner and invalidation logic.
- `tools.py` - To be modified to include helpers for fingerprinting and `uuid5` generation.
- `agents/graph_generator.py` - To be updated to consume the new deterministic plan.
- `graph.py` - The routing logic needs to be adapted for partial invalidation.
- `test/test_dynamic_planner.py` - New test file to be created for the acceptance tests.

### Notes

- Unit tests should be created to validate the new planner logic against the acceptance criteria in the PRD.
- Use `pytest` to run the new test file.

## Tasks

- [ ] 1.0 Update State Definition
  - [x] 1.1 Add `uuidPlan: List[Dict[str, str]]` to the `State` TypedDict in `state.py`.
  - [x] 1.2 Add `slotTypeMap: Dict[str, str]` to the `State` TypedDict in `state.py`.
  - [x] 1.3 Add `recordFingerprints: List[str]` to the `State` TypedDict.
  - [x] 1.4 Add `plannerVersion: str` to the `State` TypedDict in `state.py`.
  - [x] 1.5 Initialize these new fields with appropriate default values (e.g., `None`, `{}`, `[]`) in the `DEFAULT_STATE` dictionary.

- [ ] 2.0 Implement Core Planner Logic
  - [ ] 2.1 In `tools.py`, create a helper function to generate a SHA-256 fingerprint from a canonical JSON representation of a record.
  - [ ] 2.2 In `tools.py`, refactor the planning logic to use `uuid.uuid5` with a dedicated namespace for both record UUIDs and slot UUIDs.
  - [ ] 2.3 In `agents/uuid_planner.py`, update `uuid_planner_node` to calculate fingerprints for all input records and compare them against the state to detect new, changed, or removed records.
  - [ ] 2.4 Implement the ontology-driven slot derivation logic to determine the required class and facet slots for each record.
  - [ ] 2.5 Add logic to the planner to create slots for `uco-observable:ObservableRelationship` nodes when required by the `ontologyMap`.
  - [ ] 2.6 Ensure the planner node correctly returns the `uuidPlan`, `slotTypeMap`, and `recordFingerprints`.

- [ ] 3.0 Integrate Planner with Graph Generator
  - [ ] 3.1 In `agents/graph_generator.py`, modify `graph_generator_node` to receive the `uuidPlan` and `slotTypeMap` from the state.
  - [ ] 3.2 Implement logic to build a graph skeleton from the `uuidPlan` and `slotTypeMap` before populating properties.
  - [ ] 3.3 Ensure the existing logic for property placement (object vs. facet) is preserved and applied to the new graph skeleton.

- [ ] 4.0 Adapt Graph Routing for Incremental Updates
  - [ ] 4.1 In `agents/uuid_planner.py`, update `invalidate_uuid_plan_node` to optionally accept specific identifiers to allow for partial plan invalidation.
  - [ ] 4.2 In `graph.py`, update the routing logic from the `validator_node` to pass the necessary information for partial invalidation.
  - [ ] 4.3 Ensure the `route_supervisor` function handles an empty `uuidPlan` as a valid, completed state.

- [ ] 5.0 Develop Acceptance Tests
  - [ ] 5.1 Create the new test file `test/test_dynamic_planner.py`.
  - [ ] 5.2 Write a test to verify that identical input consistently produces an identical `uuidPlan` and `slotTypeMap`.
  - [ ] 5.3 Write tests to verify the incremental logic (add, update, delete records) and ensure only the necessary parts of the plan are affected.
  - [ ] 5.4 Write a test to confirm that changes in the ontology (e.g., adding a facet) correctly trigger re-planning for affected records.

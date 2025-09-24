import uuid
from typing import TypedDict, Annotated, Literal, List

from langgraph.graph import StateGraph, END

# =============================================================================
# Step 1: Define a simple State and a log for the test
# =============================================================================
class MockState(TypedDict):
    uuidPlan: List[str]
    correction_attempts: int
    # Test control
    mock_validation_error_type: Literal["none", "content", "id"]
    # Test output
    run_log: List[List[str]]

# =============================================================================
# Step 2: Create the mock nodes for the simulation
# =============================================================================

def mock_uuid_planner_node(state: MockState) -> dict:
    """Generates a UUID plan, logs it, and saves it to the state."""
    print("--- Running mock_uuid_planner_node ---")
    run_log = state.get("run_log", [])
    # This node is now the sole source of truth for creating plans.
    print("   - Generating a new plan.")
    new_plan = [f"kb:mock-id-{uuid.uuid4()}" for _ in range(2)]
    print(f"   - New plan: {new_plan}")
    run_log.append(new_plan)
    return {"uuidPlan": new_plan, "run_log": run_log}

def mock_invalidate_uuid_plan_node(state: MockState) -> dict:
    """A special node to clear the UUID plan, preparing for regeneration."""
    print("--- Running mock_invalidate_uuid_plan_node ---")
    print("   - Invalidating the current UUID plan.")
    return {"uuidPlan": None} # Setting to None ensures the planner will run again

def mock_graph_generator_node(state: MockState) -> dict:
    """Simulates generating a graph, incrementing attempts."""
    print("--- Running mock_graph_generator_node ---")
    plan = state["uuidPlan"]
    print(f"   - Using UUID Plan: {plan}")
    return {"correction_attempts": state.get("correction_attempts", 0) + 1}

def mock_validator_node(state: MockState) -> dict:
    """Simulates validating the graph and providing feedback. Passes on the second attempt."""
    print("--- Running mock_validator_node ---")
    error_type = state["mock_validation_error_type"]

    # The generator runs before this, so attempts are 1 on the first validation.
    # We want to fail on the first attempt (attempts==1) and pass on the second (attempts==2).
    if state["correction_attempts"] > 1:
        print("   - Validation PASSED (on a subsequent attempt).")
        return {"validation_feedback": ""}

    # On the first run (correction_attempts == 1), fail as dictated by the scenario.
    if error_type == "none":
        print("   - Validation PASSED.")
        return {"validation_feedback": ""}
    elif error_type == "content":
        print("   - Validation FAILED: Found a content error.")
        return {"validation_feedback": "The property 'name' has an incorrect value."}
    elif error_type == "id":
        print("   - Validation FAILED: Found an ID error.")
        return {"validation_feedback": "Duplicate @id found in graph."}
    return {}

# =============================================================================
# Step 3: Create the new routing logic for the simulation
# =============================================================================

def route_after_validation(state: MockState) -> Literal["__end__", "invalidate_plan", "generator"]:
    """
    The new, intelligent router that inspects feedback to decide the next step.
    """
    print("--- Running router: route_after_validation ---")
    feedback = state.get("validation_feedback", "")

    if not feedback:
        print("   - Decision: No feedback. Workflow ends.")
        return END

    # The core logic being tested:
    id_error_keywords = ["@id", "uuid", "identifier", "reference"]
    if any(keyword in feedback.lower() for keyword in id_error_keywords):
        print("   - Decision: ID-related error detected. Invalidating plan.")
        return "invalidate_plan"
    else:
        print("   - Decision: Content error detected. Re-running generator with stable IDs.")
        return "generator"

# =============================================================================
# Step 4: Build the test graph
# =============================================================================

builder = StateGraph(MockState)
builder.add_node("planner", mock_uuid_planner_node)
builder.add_node("generator", mock_graph_generator_node)
builder.add_node("validator", mock_validator_node)
builder.add_node("invalidate_plan", mock_invalidate_uuid_plan_node)

builder.set_entry_point("planner")
builder.add_edge("planner", "generator")
builder.add_edge("generator", "validator")
builder.add_edge("invalidate_plan", "planner")
builder.add_conditional_edges("validator", route_after_validation)

test_graph = builder.compile()

# =============================================================================
# Step 5: Run the scenarios and assert the results
# =============================================================================

def run_test_scenario(name: str, error_type: Literal["none", "content", "id"]) -> bool:
    print("\n" + "="*80)
    print(f"🧪 SCENARIO: {name}")
    print("="*80)

    initial_state = {
        "uuidPlan": None,
        "correction_attempts": 0,
        "mock_validation_error_type": error_type,
        "run_log": [],
    }

    # Use invoke to get the final state directly
    final_state = test_graph.invoke(initial_state, {"recursion_limit": 10})

    print("\n" + "-"*30)
    run_log = final_state.get("run_log", [])
    print(f"UUID Plans Generated ({len(run_log)}): {run_log}")
    print("-"*30)

    if error_type == "content":
        # Expect 1 plan, reused for the retry
        if len(run_log) == 1 and run_log[0]:
            print("✅ PASSED: UUIDs remained stable for a content-related error (only one plan was generated).")
            return True
        else:
            print(f"❌ FAILED: Expected 1 UUID plan to be generated, but found {len(run_log)}.")
            return False
    elif error_type == "id":
        # Expect 2 different plans
        if len(run_log) == 2 and run_log[0] != run_log[1]:
            print("✅ PASSED: UUIDs were correctly invalidated and regenerated for an ID-related error.")
            return True
        else:
            print(f"❌ FAILED: Expected 2 different UUID plans to be generated, but found {len(run_log)}.")
            return False
    return True

def main():
    print("Running Test-Driven Development Simulation for UUID Stability")
    
    # Scenario 1: Test that UUIDs are stable on a non-ID error
    content_error_passed = run_test_scenario(
        name="Content Error Correction",
        error_type="content"
    )

    # Scenario 2: Test that UUIDs are regenerated on an ID error
    id_error_passed = run_test_scenario(
        name="ID Error Correction",
        error_type="id"
    )

    print("\n" + "="*80)
    print("🏁 SIMULATION COMPLETE 🏁")
    print("="*80)
    if content_error_passed and id_error_passed:
        print("✅✅✅ All scenarios passed. The proposed logic is sound.")
        print("It is now safe to implement this in the production code.")
    else:
        print("❌❌❌ One or more scenarios failed. The logic needs revision before implementation.")

if __name__ == "__main__":
    main()
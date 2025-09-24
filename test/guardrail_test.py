# test/guardrail_test.py
import json
import sys
from pathlib import Path

# Add project root to sys.path to allow for module imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from graph import graph # Import the compiled graph
from state import State, DEFAULT_STATE
from config import MAX_VALIDATION_ATTEMPTS

def run_guardrail_test():
    """
    This test verifies that the routing logic correctly handles guardrails,
    specifically the MAX_VALIDATION_ATTEMPTS scenario.
    """
    print("="*80)
    print("🧪 RUNNING GUARDRAIL TEST: MAX VALIDATION ATTEMPTS 🧪")
    print("="*80)

    # --- Setup: Create a state where validation has failed and attempts are maxed out ---
    initial_state = DEFAULT_STATE.copy()
    initial_state.update({
        'messages': [('user', 'This is a test for max validation attempts guardrail.')],
        'ontologyMap': {"analysis": "complete", "additional_details": {}},
        'ontologyMarkdown': "# Mock Markdown",
        'customFacets': {},
        'customState': {},
        'jsonldGraph': {"@graph": ["This is a mock graph that will fail validation."]},
        'validation_result': {"is_clean": False}, # Mock that validation has failed
        'validationAttempts': MAX_VALIDATION_ATTEMPTS, # Mock that attempts are maxed out
    })

    print("\n📝 INITIAL STATE:")
    print(f"- Workflow should be at the validation step.")
    print(f"- Validation has failed (`is_clean`: False).")
    print(f"- Validation attempts are at their maximum ({MAX_VALIDATION_ATTEMPTS}).")
    print("EXPECTED OUTCOME: The router should see that attempts are maxed out and terminate the workflow ('__end__').")
    print("-" * 80)

    # --- Execute the workflow ---
    print("\n🚀 EXECUTING AGENT WORKFLOW...")
    path = []
    config = {"recursion_limit": 100}

    for event in graph.stream(initial_state, config):
        node_name = list(event.keys())[0]
        path.append(node_name)
        print(f" -> Executing node: {node_name}")

    print("-" * 80)

    # --- Analyze the result ---
    print("\n📊 ANALYSIS:")
    print(f"  - Final execution path: {' -> '.join(path)}")

    # In this specific test, the router should be called immediately after the 'supervisor'
    # entry node and decide to terminate. So, a short path of ['supervisor'] is the expected success.
    if len(path) == 1 and path[0] == 'supervisor':
        print("  - ✅ PASSED: The router correctly decided to terminate the workflow immediately, and the graph did not loop.")
        print("  - The log '⚠️ [ROUTER] State: Max validation attempts reached. -> __end__' confirms the correct decision was made.")
    else:
        print(f"  - ❌ FAILED: The workflow did not terminate as expected. The path was: {' -> '.join(path)}")

    print("="*80)
    print("🏁 GUARDRAIL TEST COMPLETE 🏁")
    print("="*80)


if __name__ == "__main__":
    run_guardrail_test()

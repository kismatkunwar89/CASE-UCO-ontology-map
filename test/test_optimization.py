# test/test_optimization.py
import sys
from pathlib import Path

# Add project root to sys.path to allow for module imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from graph import graph
from state import DEFAULT_STATE

def run_optimization_test():
    """
    This test runs a simple, successful workflow from start to finish
    and counts the number of nodes executed. It serves as a benchmark.
    """
    print("="*80)
    print("🧪 RUNNING WORKFLOW PERFORMANCE TEST 🧪")
    print("="*80)

    # --- Setup: A simple input that requires no custom facets or retries ---
    initial_state = DEFAULT_STATE.copy()
    initial_state.update({
        'messages': [('user', 'A simple test case')],
        # This mock map indicates ontology research is done and no custom facets are needed
        'ontologyMap': {
            "analysis": "complete",
            "additional_details": { "unmappedElements": [] }
        },
        'ontologyMarkdown': "# Mock Markdown",
    })

    # --- Execute the workflow ---
    path = []
    config = {"recursion_limit": 100}

    # This loop will be different after optimization, but the logic remains
    for event in graph.stream(initial_state, config):
        node_name = list(event.keys())[0]
        if node_name != '__end__': # Don't count the end state as a node
            path.append(node_name)

    # --- Report the results ---
    print("\n📊 EXECUTION ANALYSIS:")
    print(f"  - Execution path: {" -> ".join(path)}")
    print(f"  - TOTAL NODES EXECUTED: {len(path)}")
    print("="*80)

if __name__ == "__main__":
    run_optimization_test()

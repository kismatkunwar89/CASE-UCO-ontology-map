
import json
import sys
from pathlib import Path

# Add project root to sys.path to allow for module imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from services import call_forensic_analysis_with_session

def run_end_to_end_test():
    """
    Runs a full, end-to-end test of the agentic workflow, from input to final graph.
    This test helps in debugging the flow and identifying optimization opportunities.
    """
    print("="*80)
    print("🧪 STARTING END-TO-END AGENT FLOW TEST 🧪")
    print("="*80)

    # 1. Define the test case input
    # Using the complex MFT records example
    user_identifier = "e2e_test_user"
    input_artifacts = {
      "artifact_type": "MFT Records",
      "description": "Master File Table records",
      "source": "NTFS filesystem analysis",
      "records": [
        {
          "EntryNumber": 42,
          "SequenceNumber": 3,
          "ParentEntryNumber": 5,
          "FullPath": "\\Windows\\Prefetch\\MALICIOUS.EXE-12345678.pf",
          "InUse": True,
          "SI_Created": "2025-09-17T10:30:00Z",
          "SI_Modified": "2025-09-17T10:35:15Z",
          "SI_Accessed": "2025-09-17T10:35:15Z",
          "FN_Created": "2025-09-17T10:30:00Z",
          "FN_Modified": "2025-09-17T10:35:15Z"
        },
        {
          "EntryNumber": 314,
          "SequenceNumber": 1,
          "ParentEntryNumber": 200,
          "FullPath": "\\Users\\Alice\\Documents\\report.docx",
          "InUse": True,
          "SI_Created": "2024-10-05T09:12:00Z",
          "SI_Modified": "2025-01-20T16:33:11Z",
          "SI_Accessed": "2025-01-22T07:02:45Z",
          "FN_Created": "2024-10-05T09:12:00Z",
          "FN_Modified": "2025-01-20T16:33:11Z"
        }
      ]
    }

    print("\n📝 TEST INPUT:")
    print(json.dumps(input_artifacts, indent=2))
    print("-" * 80)

    # 2. Execute the full agent session
    print("\n🚀 EXECUTING AGENT WORKFLOW...")
    print("(This will show all intermediate steps for debugging)")
    print("-" * 80)

    try:
        # The `call_forensic_analysis_with_session` function runs the entire graph
        result = call_forensic_analysis_with_session(
            user_identifier=user_identifier,
            input_artifacts=input_artifacts,
            show_all_steps=True  # Set to True to get verbose output for debugging
        )
        print("-" * 80)
        print("✅ WORKFLOW EXECUTION FINISHED")
        print("-" * 80)

        # 3. Analyze and report the results
        final_state = result.get("final_state", {})
        if not final_state:
            print("❌ TEST FAILED: No final state was returned.")
            return

        print("\n📊 FINAL RESULTS & ANALYSIS:")
        print("-" * 80)

        # Print key metrics for optimization
        print("📈 Performance Metrics:")
        print(f"  - Session ID: {result.get('session_id')}")
        print(f"  - Total Steps: {result.get('total_steps')}")
        print("  - Ontology Research: Completed")
        print(f"  - Custom Facet Attempts: {final_state.get('customFacetAttempts', 'N/A')}")
        print(f"  - Graph Generator Attempts: {final_state.get('graphGeneratorAttempts', 'N/A')}")
        print(f"  - Validation Attempts: {final_state.get('validationAttempts', 'N/A')}")
        print(f"  - Hallucination Check Attempts: {final_state.get('layer2_attempts', 'N/A')}")
        print("-" * 30)

        # Check for errors
        errors = {
            "custom": final_state.get("customFacetErrors"),
            "graph": final_state.get("graphGeneratorErrors"),
            "validation": final_state.get("validationErrors"),
            "hallucination": final_state.get("hallucinationErrors")
        }
        has_errors = any(e for e in errors.values())
        if has_errors:
            print("⚠️ ERRORS DETECTED DURING WORKFLOW:")
            for agent, error_list in errors.items():
                if error_list:
                    print(f"  - {agent.capitalize()} Errors: {error_list}")
            print("-" * 30)

        # Print the final generated graph
        final_graph = final_state.get("jsonldGraph")
        if final_graph:
            print("📋 FINAL GENERATED JSON-LD GRAPH:")
            print(json.dumps(final_graph, indent=2))
        else:
            print("❌ FINAL GRAPH NOT FOUND IN STATE.")

        print("\n" + "="*80)
        print("🏁 END-TO-END TEST COMPLETE 🏁")
        print("="*80)

    except Exception as e:
        print("\n" + "="*80)
        print(f"❌ TEST FAILED WITH AN EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        print("="*80)


if __name__ == "__main__":
    run_end_to_end_test()

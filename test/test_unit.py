# test/test_unit.py
import unittest
import json
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Functions and classes to test
from utils import parse_ontology_response
from graph import route_supervisor, route_after_validation
from config import MAX_VALIDATION_ATTEMPTS
from state import DEFAULT_STATE

class TestCoreLogic(unittest.TestCase):

    def test_parser_selects_last_json(self):
        """Verify the parser ignores initial JSON blocks and selects the last one."""
        print("\n--- Testing: Parser Logic ---")
        report_content = """
        Some text...
        ```json
        {"key": "first_json_block"}
        ```
        More text...
        ```json
        {"key": "second_and_correct_json_block"}
        ```
        """
        parsed = parse_ontology_response(report_content)
        self.assertEqual(parsed.get("key"), "second_and_correct_json_block")
        print("✅ PASSED: Parser correctly selected the last JSON block.")

    def test_router_sends_to_ontology(self):
        """Verify the router directs to ontology_research_node when state is empty."""
        print("\n--- Testing: Router Logic (Empty State) ---")
        state = DEFAULT_STATE.copy()
        decision = route_supervisor(state)
        self.assertEqual(decision, "ontology_research_node")
        print("✅ PASSED: Router correctly chose 'ontology_research_node' for an empty state.")

    def test_router_sends_to_custom_facet(self):
        """Verify the router directs to custom_facet_node after ontology is done."""
        print("\n--- Testing: Router Logic (Ontology Done) ---")
        state = DEFAULT_STATE.copy()
        state['ontologyMap'] = {"status": "done"}
        state['ontologyMarkdown'] = "report"
        decision = route_supervisor(state)
        self.assertEqual(decision, "custom_facet_node")
        print("✅ PASSED: Router correctly chose 'custom_facet_node'.")

    def test_router_sends_to_validator(self):
        """Verify the router directs to validator_node when appropriate."""
        print("\n--- Testing: Router Logic (Ready for Validation) ---")
        state = DEFAULT_STATE.copy()
        state['ontologyMap'] = {"status": "done"}
        state['ontologyMarkdown'] = "report"
        state['customFacets'] = {}
        state['jsonldGraph'] = {"@graph": []}
        state['validation_result'] = {"is_clean": False} # Not clean yet
        decision = route_supervisor(state)
        self.assertEqual(decision, "validator_node")
        print("✅ PASSED: Router correctly chose 'validator_node'.")

    def test_router_validation_guardrail(self):
        """Verify the router terminates when max validation attempts are reached."""
        print("\n--- Testing: Router Logic (Validation Guardrail) ---")
        state = DEFAULT_STATE.copy()
        state['ontologyMap'] = {"status": "done"}
        state['ontologyMarkdown'] = "report"
        state['customFacets'] = {}
        state['jsonldGraph'] = {"@graph": []}
        state['validation_result'] = {"is_clean": False}
        state['validationAttempts'] = MAX_VALIDATION_ATTEMPTS
        decision = route_supervisor(state)
        self.assertEqual(decision, "__end__")
        print("✅ PASSED: Router correctly terminated after max validation attempts.")

    def test_router_success_path(self):
        """Verify the router correctly identifies a successful state before hallucination check."""
        print("\n--- Testing: Router Logic (Pre-Hallucination Success) ---")
        state = DEFAULT_STATE.copy()
        state['ontologyMap'] = {"status": "done"}
        state['ontologyMarkdown'] = "report"
        state['customFacets'] = {}
        state['jsonldGraph'] = {"@graph": []}
        state['validation_result'] = {"is_clean": True} # is_clean is True
        
        # After successful validation, the next step is hallucination check
        # This is handled by `route_after_validation`, not the main supervisor
        decision = route_after_validation(state)
        self.assertEqual(decision, "hallucination_check_node")
        print("✅ PASSED: Router correctly identified the next step is 'hallucination_check_node'.")


if __name__ == '__main__':
    print("="*80)
    print("🔬 RUNNING UNIT TESTS FOR CORE LOGIC 🔬")
    print("="*80)
    unittest.main()

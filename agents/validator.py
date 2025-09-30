import json
import re
from datetime import datetime
from typing import Literal

from langchain_core.messages import HumanMessage

# --- Custom Module Imports ---
from state import State
from config import llm, MAX_VALIDATION_ATTEMPTS
from utils import RE_FENCED_JSON
from tools import validate_case_jsonld
from feedback_utils import categorize_validation_feedback


# =============================================================================
# Agent Node Function
# =============================================================================

def validator_node(state: State) -> dict:
    """
    Performs Layer 1 validation on the generated JSON-LD graph.
    This now includes a programmatic check for correct property placement.
    """
    current_attempts = state.get("validationAttempts", 0)
    validation_errors = state.get("validationErrors", [])
    validation_history = state.get("validationHistory", [])

    print(
        f"[INFO] [Validator] Attempt {current_attempts + 1}/{MAX_VALIDATION_ATTEMPTS}")

    if current_attempts >= MAX_VALIDATION_ATTEMPTS:
        print("[WARNING] [Validator] Max attempts reached.")
        return {}

    jsonld_graph = state.get("jsonldGraph")
    ontology_map = state.get("ontologyMap", {})

    if not jsonld_graph or not isinstance(jsonld_graph.get("@graph"), list):
        print("[ERROR] [Validator] No valid JSON-LD graph to validate.")
        return {"validation_feedback": "No valid JSON-LD graph found in state."}

    hard_feedback_items = []  # Critical errors (Violations, Warnings, misplaced properties)
    soft_feedback_items = []  # Informational suggestions (Info messages)

    # --- 1. Dynamic, Programmatic check for misplaced properties (always HARD feedback) ---
    try:
        # Get all properties that are defined as belonging to a facet
        all_facet_properties = set()
        if isinstance(ontology_map.get("properties"), dict):
            for owner, props in ontology_map["properties"].items():
                # Assume an owner is a facet if its name ends with 'Facet'
                if owner.endswith("Facet"):
                    all_facet_properties.update(props)

        if all_facet_properties:
            for node in jsonld_graph["@graph"]:
                # Check any node that is NOT a facet itself
                node_type = node.get("@type", "")
                if not isinstance(node_type, str) or not node_type.endswith("Facet"):
                    # Find any properties in this node that should belong to a facet
                    node_props = set(node.keys())
                    # We need to map from the prompt's property names (e.g., 'filePath') to the graph's (e.g., 'uco-observable:filePath')
                    # For now, we do a simple substring check as a heuristic.
                    for facet_prop_base in all_facet_properties:
                        for node_prop_full in node_props:
                            if facet_prop_base in node_prop_full:
                                hard_feedback_items.append(
                                    f"Invalid property placement on node '{node.get('@id')}' of type '{node_type}'. "
                                    f"The property '{node_prop_full}' likely belongs on a Facet, not the parent object."
                                )
    except Exception as e:
        hard_feedback_items.append(f"Error during programmatic property placement check: {str(e)}")


    # --- 2. External tool validation for basic syntax ---
    case_validation_result = ""
    case_conforms = False
    try:
        case_validation_result = validate_case_jsonld.invoke({
            "input_data": json.dumps(jsonld_graph, indent=2),
            "case_version": "case-1.4.0"
        })
        case_conforms = "Conforms: True" in case_validation_result or "PASSED" in case_validation_result.upper()

        # Categorize case_validate feedback into hard and soft
        if not case_conforms:
            hard_from_case, soft_from_case = categorize_validation_feedback(case_validation_result)
            hard_feedback_items.extend(hard_from_case)
            soft_feedback_items.extend(soft_from_case)
    except Exception as e:
        case_validation_result = f"CASE/UCO validation failed due to error: {str(e)}"
        hard_feedback_items.append(case_validation_result)
        case_conforms = False


    # --- 3. Combine feedback and make a decision ---
    # Validation passes if there are NO hard feedback items (soft feedback is OK)
    is_clean = len(hard_feedback_items) == 0

    # Prepare feedback strings
    if hard_feedback_items:
        final_feedback = "CRITICAL ERRORS:\n" + "\n".join(hard_feedback_items)
    else:
        final_feedback = "Layer 1 validation passed."

    validation_result = {
        "is_clean": is_clean,
        "feedback": final_feedback,
        "violations": hard_feedback_items,
        "suggestions": soft_feedback_items,
        "case_uco_result": case_validation_result,
        "case_uco_passed": case_conforms
    }

    current_attempt_record = {
        "attempt": current_attempts + 1,
        "timestamp": datetime.now().isoformat(),
        "feedback": final_feedback,
        "is_clean": is_clean,
        "case_uco_result": case_validation_result,
        "suggestions_count": len(soft_feedback_items)
    }
    updated_history = validation_history + [current_attempt_record]

    if is_clean:
        # Validation passed! Store soft feedback as suggestions for the user
        print("[SUCCESS] [Validator] Layer 1 validation passed.")
        if soft_feedback_items:
            print(f"[INFO] [Validator] Found {len(soft_feedback_items)} suggestion(s) for user.")

        preserved_result = {
            "jsonldGraph": jsonld_graph,
            "timestamp": datetime.now().isoformat()
        }

        return_dict = {
            "validation_result": validation_result,
            "layer1_preserved_result": preserved_result,
            "validationAttempts": current_attempts + 1,
            "validationHistory": updated_history,
            "messages": [HumanMessage(content="Layer 1 validation passed.", name="validator_agent")]
        }

        # Add validation suggestions if any exist
        if soft_feedback_items:
            return_dict["validation_suggestions"] = soft_feedback_items

        return return_dict
    else:
        print(f"[FAILURE] [Validator] Layer 1 validation failed: {final_feedback}")
        
        # Extract UUIDs from the feedback string to request partial invalidation
        uuids_to_invalidate = re.findall(r'kb:[a-zA-Z0-9_-]+-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', final_feedback)
        
        return_dict = {
            "validation_result": validation_result,
            "validation_feedback": final_feedback,
            "validationAttempts": current_attempts + 1,
            "validationHistory": updated_history,
            "messages": [HumanMessage(content=f"Layer 1 validation failed: {final_feedback}", name="validator_agent")]
        }
        
        if uuids_to_invalidate:
            print(f"   - Found UUIDs to invalidate: {uuids_to_invalidate}")
            return_dict["uuids_to_invalidate"] = uuids_to_invalidate
            
        return return_dict
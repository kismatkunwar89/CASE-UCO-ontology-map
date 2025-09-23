import json
from datetime import datetime
from typing import Literal

from langchain_core.messages import HumanMessage

# --- Custom Module Imports ---
from state import State
from config import llm, MAX_VALIDATION_ATTEMPTS
from utils import RE_FENCED_JSON
from tools import validate_case_jsonld
# =============================================================================
# Agent Node Function
# =============================================================================

def validator_node(state: State) -> dict:
    """
    Performs Layer 1 structural validation on the generated JSON-LD graph.
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
    if not jsonld_graph:
        print("[ERROR] [Validator] No JSON-LD graph to validate.")
        return {}

    try:
        case_validation_result = validate_case_jsonld.invoke({
            "input_data": json.dumps(jsonld_graph, indent=2),
            "case_version": "case-1.4.0"
        })
    except Exception as e:
        case_validation_result = f"CASE/UCO validation failed due to error: {str(e)}"

    validation_prompt = f"""
You are a forensic data validation expert. Validate the following JSON-LD graph...
... (prompt content) ...
CASE/UCO Validation Result: {case_validation_result}
... (prompt content) ...
"""

    try:
        validation_response = llm.invoke(
            [{"role": "user", "content": validation_prompt}])
        response_content = validation_response.content

        json_match = RE_FENCED_JSON.search(response_content)
        json_content = json_match.group(1) if json_match else response_content

        validation_result = json.loads(json_content)
        is_clean = validation_result.get("is_clean", False)

        validation_result["case_uco_result"] = case_validation_result
        validation_result["case_uco_passed"] = "Conforms: True" in case_validation_result or "PASSED" in case_validation_result.upper()

        current_attempt_record = {
            "attempt": current_attempts + 1,
            "timestamp": datetime.now().isoformat(),
            "feedback": validation_result.get("feedback", ""),
            "is_clean": is_clean,
            "case_uco_result": case_validation_result
        }
        updated_history = validation_history + [current_attempt_record]

        if is_clean:
            preserved_result = {
                "jsonldGraph": jsonld_graph,
                "timestamp": datetime.now().isoformat()
            }
            return {
                "validation_result": validation_result,
                "layer1_preserved_result": preserved_result,
                "validationAttempts": current_attempts + 1,
                "validationHistory": updated_history,
                "messages": [HumanMessage(content="Layer 1 validation passed.", name="validator_agent")]
            }
        else:
            feedback = validation_result.get("feedback", "Structural validation failed.")
            return {
                "validation_result": validation_result,
                "validation_feedback": feedback,
                "validationAttempts": current_attempts + 1,
                "validationHistory": updated_history,
                "messages": [HumanMessage(content=f"Layer 1 validation failed: {feedback}", name="validator_agent")]
            }
    except Exception as e:
        error_msg = f"Validation processing failed on attempt {current_attempts + 1}: {str(e)}"
        return {
            "validationAttempts": current_attempts + 1,
            "validationErrors": validation_errors + [error_msg],
            "validation_result": {
                "is_clean": False,
                "feedback": f"Validation error: {str(e)}",
                "case_uco_result": "Validation failed due to error",
                "case_uco_passed": False
            }
        }
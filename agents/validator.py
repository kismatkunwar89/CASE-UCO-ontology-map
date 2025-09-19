import json
from datetime import datetime
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command

# --- Custom Module Imports ---
from state import State
from config import llm, MAX_VALIDATION_ATTEMPTS
from utils import RE_FENCED_JSON
from tools import validate_case_jsonld
# =============================================================================
# Agent Node Function
# =============================================================================


def validator_node(state: State) -> Command:
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
        # Fallback logic here...
        return Command(goto="__end__")

    jsonld_graph = state.get("jsonldGraph")
    if not jsonld_graph:
        print("[ERROR] [Validator] No JSON-LD graph to validate.")
        return Command(goto="supervisor")

    # First, call the actual CASE/UCO validator tool
    print("[INFO] [Validator] Calling CASE/UCO validator tool...")
    try:
        case_validation_result = validate_case_jsonld.invoke({
            "input_data": json.dumps(jsonld_graph, indent=2),
            "case_version": "case-1.4.0"
        })
        print(
            f"[INFO] [Validator] CASE/UCO validation result: {case_validation_result[:200]}...")
    except Exception as e:
        print(f"[ERROR] [Validator] CASE/UCO tool failed: {str(e)}")
        case_validation_result = f"CASE/UCO validation failed due to error: {str(e)}"

    # Get learning context and validation feedback (exactly like complete_main_code.py)
    learning_context = state.get("learningContext", "")
    validation_feedback = state.get("validation_feedback", "")

    # Build validation history context
    history_context = ""
    if validation_history:
        history_context = f"\nPrevious validation attempts ({len(validation_history)}):\n"
        # Show last 3 attempts
        for i, attempt in enumerate(validation_history[-3:], 1):
            history_context += f"Attempt {i}: {attempt.get('feedback', 'No feedback')}\n"

    # Create validation prompt with learning context, validation feedback, and history
    validation_prompt = f"""
You are a forensic data validation expert. Validate the following JSON-LD graph for structural integrity and CASE/UCO compliance.

{learning_context}

Previous validation feedback: {validation_feedback}
{history_context}

JSON-LD Graph to validate:
{json.dumps(jsonld_graph, indent=2)}

CASE/UCO Validation Result: {case_validation_result}

Validation Criteria:
1. Structural integrity (proper JSON-LD format)
2. CASE/UCO class compliance
3. Required properties present
4. Proper relationships between entities
5. No missing or malformed data

Provide validation result in JSON format:
{{
    "is_valid": boolean,
    "conforms": boolean,
    "is_clean": boolean,
    "feedback": "detailed feedback string",
    "issues": ["list of specific issues found"],
    "recommendations": ["list of recommendations"]
}}
"""

    try:
        # Call LLM for validation (exactly like complete_main_code.py)
        validation_response = llm.invoke(
            [{"role": "user", "content": validation_prompt}])
        response_content = validation_response.content

        json_match = RE_FENCED_JSON.search(response_content)
        json_content = json_match.group(1) if json_match else response_content

        validation_result = json.loads(json_content)
        is_clean = validation_result.get("is_clean", False)

        # Add CASE/UCO result to validation_result for learning
        validation_result["case_uco_result"] = case_validation_result
        validation_result["case_uco_passed"] = "Conforms: True" in case_validation_result or "PASSED" in case_validation_result.upper()

        # Update validation history with current attempt (for learning)
        current_attempt_record = {
            "attempt": current_attempts + 1,
            "timestamp": datetime.now().isoformat(),
            "feedback": validation_result.get("feedback", ""),
            "is_clean": is_clean,
            "case_uco_result": case_validation_result
        }
        updated_history = validation_history + [current_attempt_record]

        if is_clean:
            print("[SUCCESS] [Validator] Layer 1 structural validation passed.")
            preserved_result = {
                "jsonldGraph": jsonld_graph,
                "timestamp": datetime.now().isoformat()
            }
            return Command(
                update={
                    "validation_result": validation_result,
                    "layer1_preserved_result": preserved_result,
                    "validationAttempts": current_attempts + 1,
                    "validationHistory": updated_history,
                    "messages": [HumanMessage(content="Layer 1 validation passed.", name="validator_agent")]
                },
                goto="hallucination_check_node"
            )
        else:
            feedback = validation_result.get(
                "feedback", "Structural validation failed.")
            print(
                f"[WARNING] [Validator] Layer 1 validation failed. Feedback: {feedback}")
            return Command(
                update={
                    "validation_result": validation_result,
                    "validation_feedback": feedback,
                    "validationAttempts": current_attempts + 1,
                    "validationHistory": updated_history,
                    "messages": [HumanMessage(content=f"Layer 1 validation failed: {feedback}", name="validator_agent")]
                },
                goto="supervisor"
            )
    except Exception as e:
        error_msg = f"Validation processing failed on attempt {current_attempts + 1}: {str(e)}"
        print(f"[ERROR] [Validator] {error_msg}")
        return Command(
            update={
                "validationAttempts": current_attempts + 1,
                "validationErrors": validation_errors + [error_msg],
                "validation_result": {
                    "is_clean": False,
                    "feedback": f"Validation error: {str(e)}",
                    "case_uco_result": "Validation failed due to error",
                    "case_uco_passed": False
                }
            },
            goto="supervisor"
        )

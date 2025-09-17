import json
from datetime import datetime
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command

# --- Custom Module Imports ---
from state import State
from config import llm, MAX_VALIDATION_ATTEMPTS
from utils import RE_FENCED_JSON

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

    validation_prompt = f"""
You are a forensic data validation expert. Validate the following JSON-LD graph for structural integrity and CASE/UCO compliance.

JSON-LD Graph to validate:
{json.dumps(jsonld_graph, indent=2)}

Validation Criteria:
1. Structural integrity (proper JSON-LD format)
2. CASE/UCO class compliance
3. Required properties present

Provide validation result in a JSON format with keys: "is_clean" (boolean) and "feedback" (string).
"""

    try:
        response_content = llm.invoke(validation_prompt).content

        json_match = RE_FENCED_JSON.search(response_content)
        json_content = json_match.group(1) if json_match else response_content

        validation_result = json.loads(json_content)
        is_clean = validation_result.get("is_clean", False)

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
            },
            goto="supervisor"
        )


import re
import json
from typing import Dict, Any
# =============================================================================
# Essential Helper Functions
# =============================================================================


def _msg_text(msg):
    """Safely extract text content from BaseMessage objects."""
    if isinstance(msg, (list, tuple)):
        # Walk newest-to-oldest and return the first readable content, preferring human turns.
        for item in reversed(msg):
            if getattr(item, "type", None) == "human" and hasattr(item, "content"):
                return item.content
        # Fall back to any message with content/text.
        for item in reversed(msg):
            if hasattr(item, "content"):
                return item.content
            if hasattr(item, "text"):
                return item.text
        return ""

    if hasattr(msg, 'content'):
        return msg.content
    if hasattr(msg, 'text'):
        return msg.text
    if isinstance(msg, str):
        return msg
    return str(msg)


def _get_input_artifacts(state):
    """Extract input artifacts from the state messages, rawInputJSON, or input_artifacts."""
    # First try rawInputJSON
    raw = state.get("rawInputJSON")
    if raw is None:
        raw = state.get("input_artifacts")  # fallback to input_artifacts
    if raw is not None:
        # Convert to string if it's a dict/list
        if isinstance(raw, (dict, list)):
            return json.dumps(raw, indent=2)
        return str(raw)

    # Fallback to messages if available
    if "messages" in state and state["messages"]:
        first_msg = state["messages"][0]
        return _msg_text(first_msg)
    return ""

# =============================================================================
# Parser Functions
# =============================================================================


RE_FENCED_JSON = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_ontology_response(content: str) -> Dict[str, Any]:
    """
    Parse the LLM response to extract the final JSON block for ontology mapping.
    It specifically targets the *last* JSON block in the content.
    """
    # Find all non-overlapping matches of JSON blocks
    matches = RE_FENCED_JSON.findall(content)

    if matches:
        last_json_block = matches[-1]
        try:
            data = json.loads(last_json_block)
            return data
        except json.JSONDecodeError as e:
            print(f"[WARNING] [Parser] Initial JSON parsing failed: {e}. Attempting to repair...")
            try:
                # Attempt to find the last valid JSON object and parse that
                last_brace_index = last_json_block.rfind('}')
                if last_brace_index != -1:
                    repaired_json = last_json_block[:last_brace_index + 1]
                    data = json.loads(repaired_json)
                    print("[INFO] [Parser] Successfully parsed repaired JSON.")
                    return data
                else:
                    raise e # Re-raise if no closing brace is found
            except json.JSONDecodeError as final_e:
                error_message = f"Malformed JSON block found in agent response: {final_e}. Content: '{last_json_block[:200]}...'"
                print(f"[ERROR] [Parser] {error_message}")
                return {"error": error_message}

    # Fallback if no JSON block is found at all
    return {"error": "No JSON block found in the agent response."}

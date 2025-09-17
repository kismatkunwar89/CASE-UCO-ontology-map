
import re
import json
from typing import Dict, Any
# =============================================================================
# Essential Helper Functions
# =============================================================================


def _msg_text(msg):
    """Safely extract text content from BaseMessage objects."""
    if hasattr(msg, 'content'):
        return msg.content
    elif hasattr(msg, 'text'):
        return msg.text
    elif isinstance(msg, str):
        return msg
    else:
        return str(msg)


def _get_input_artifacts(state):
    """Extract input artifacts from the state messages."""
    if "messages" in state and state["messages"]:
        first_msg = state["messages"][0]
        return _msg_text(first_msg)
    return ""

# =============================================================================
# Parser Functions
# =============================================================================


RE_FENCED_JSON = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def parse_ontology_response(content: str, input_text: str) -> Dict[str, Any]:
    """Parse the LLM response to extract the JSON block for ontology mapping."""
    m = RE_FENCED_JSON.search(content)
    if m:
        try:
            data = json.loads(m.group(1))
            return {
                "input_text": input_text,
                "artifacts": data.get("artifacts", []),
                "classes": data.get("classes", []),
                "properties": data.get("properties", {}),
                "facets": data.get("facets", []),
                "relationships": data.get("relationships", []),
                "additional_details": {"markdown": content}
            }
        except json.JSONDecodeError:
            # If JSON is malformed, fall through to the fallback
            pass

    # Fallback if no JSON is found or if parsing fails
    return {
        "input_text": input_text,
        "artifacts": [],
        "classes": [],
        "properties": {},
        "facets": [],
        "relationships": [],
        "additional_details": {"markdown": content}
    }

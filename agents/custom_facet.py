import json
import re
from typing import Any, Dict, Literal, Optional

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from pydantic import BaseModel, Field

# --- Custom Module Imports ---
from state import State
from config import MAX_CUSTOM_FACET_ATTEMPTS, CUSTOM_FACET_AGENT_PROMPT


class CustomFacetResponse(BaseModel):
    """Structured schema for the custom facet agent."""

    customFacets: Dict[str, Any] = Field(default_factory=dict)
    customState: Dict[str, Any] = Field(default_factory=dict)
    ttlDefinitions: Optional[str] = None


_CODE_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_LINE_COMMENT_PATTERN = re.compile(r"(?<!https:)(?<!http:)//.*")


def _model_dump(model: CustomFacetResponse) -> Dict[str, Any]:
    """Compatible dump for both Pydantic v1 and v2."""

    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _extract_json_payload(text: str) -> Dict[str, Any]:
    """Attempt to coerce a JSON payload out of an LLM text response."""

    match = _CODE_FENCE_PATTERN.search(text)
    candidate = match.group(1) if match else text
    candidate = candidate.strip()

    # Trim leading / trailing content outside the outermost braces
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object detected in custom facet response")
    candidate = candidate[start : end + 1]

    # Drop simple line comments that sometimes appear in model output
    cleaned_lines = []
    for line in candidate.splitlines():
        cleaned_lines.append(_LINE_COMMENT_PATTERN.sub("", line))
    cleaned = "\n".join(cleaned_lines)

    return json.loads(cleaned)

# =============================================================================
# Agent Setup
# =============================================================================

custom_facet_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
custom_facet_structured_llm = custom_facet_llm.with_structured_output(
    CustomFacetResponse, method="function_calling"
)

# =============================================================================
# Agent Node Function
# =============================================================================

def custom_facet_node(state: State) -> dict:
    """
    Analyzes the initial input and ontology map to determine if custom
    facets are needed, then generates them.
    """
    current_attempts = state.get("customFacetAttempts", 0)
    custom_errors = state.get("customFacetErrors", [])

    print(
        f"[INFO] [Custom Facet] Attempt {current_attempts + 1}/{MAX_CUSTOM_FACET_ATTEMPTS}")

    if current_attempts >= MAX_CUSTOM_FACET_ATTEMPTS:
        print(
            f"[WARNING] [Custom Facet] Max attempts reached. Proceeding with empty custom facets.")
        return {
            "customFacets": {},
            "customState": {
                "reasoning": f"Max attempts ({MAX_CUSTOM_FACET_ATTEMPTS}) reached",
                "errors": custom_errors
            },
            "customFacetAttempts": current_attempts
        }

    if state.get("customFacets") is not None and not custom_errors:
        print("[INFO] [Custom Facet] Step already complete, skipping.")
        return {}

    ontology_map = state.get("ontologyMap", {})

    # --- FAIL-FAST GUARDRAIL ---
    if "error" in ontology_map:
        print("[ERROR] [Custom Facet] Received an error from the previous node. Halting execution.")
        return {
            "customFacetErrors": custom_errors + ["Received an error from ontology_research_agent."],
        }

    # Get both the original input and the first agent's map for full context
    messages = state.get("messages", [])
    original_input = next((str(m.content) for m in messages if hasattr(m, 'type') and m.type == "human"), "")

    # --- FAST PATH OPTIMIZATION ---
    additional_details = ontology_map.get("additional_details") or {}
    reserved_fields = {"artifact_type", "description", "source"}
    raw_unmapped = additional_details.get("unmappedElements", [])
    unmapped_elements = [
        element
        for element in raw_unmapped
        if not isinstance(element, str) or element not in reserved_fields
    ]

    if not unmapped_elements:
        print("[INFO] [Custom Facet] Pre-check PASSED: Agent 1 mapped all elements. Skipping LLM analysis.")
        return {
            "customFacets": {},
            "customState": {
                "totalCustomFacets": 0,
                "extensionNamespace": "dfc-ext",
                "reasoningApplied": False, 
                "customFacetsNeeded": False,
                "dataCoverageComplete": True,
                "reasoning": "All data elements successfully mapped by ontology_research_agent."
            },
            "customFacetAttempts": current_attempts + 1,
        }
    # --- END OF FAST PATH ---

    print("[INFO] [Custom Facet] Starting independent reasoning analysis...")

    error_feedback = ""
    if custom_errors:
        error_feedback = f"\n\nPREVIOUS ERRORS TO CONSIDER:\n" + "\n".join(custom_errors[-2:])

    # New, clearer prompt with distinct roles for each piece of information
    prompt = f"""
**CONTEXT: ORIGINAL USER INPUT**
This is the complete, original data provided by the user. Use this for context if you need to understand an unmapped element.
```json
{original_input}
```

**TASK: ANALYZE AGENT 1'S OUTPUT**
This is the analysis from the first agent. Your job is to find any gaps it left.
```json
{json.dumps(ontology_map, indent=2)}
```
{error_feedback}

**YOUR INSTRUCTIONS**
1. Look at the `unmappedElements` list in the "ANALYZE AGENT 1'S OUTPUT" section.
2. If the list is empty, your job is done. Return an empty `customFacets` object.
3. If the list is NOT empty, use the "ORIGINAL USER INPUT" to understand the context of the unmapped elements and create custom facets for them.
"""

    try:
        print("[INFO] [Custom Facet] Sending prompt via structured output...")

        data: Dict[str, Any]
        try:
            response_model = custom_facet_structured_llm.invoke([
                {"role": "system", "content": CUSTOM_FACET_AGENT_PROMPT},
                {"role": "user", "content": prompt},
            ])
            data = _model_dump(response_model)
            print("[INFO] [Custom Facet] Structured output received.")
        except Exception as structured_err:
            print(
                f"[WARNING] [Custom Facet] Structured output failed: {structured_err}. Falling back to raw parsing."
            )
            raw_response = custom_facet_llm.invoke(
                [
                    {"role": "system", "content": CUSTOM_FACET_AGENT_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            )
            raw_text = getattr(raw_response, "content", raw_response)
            try:
                data = _extract_json_payload(raw_text)
                print("[INFO] [Custom Facet] Successfully parsed fallback JSON response.")
            except Exception as fallback_err:
                error_msg = (
                    f"Processing failed on attempt {current_attempts + 1}: "
                    f"Unable to parse custom facet JSON ({fallback_err})."
                )
                print(f"[ERROR] [Custom Facet] {error_msg}")
                new_errors = custom_errors + [error_msg]
                return {
                    "customFacetAttempts": current_attempts + 1,
                    "customFacetErrors": new_errors,
                    "messages": [
                        HumanMessage(content=error_msg, name="custom_facet_agent")
                    ],
                }

        custom_facets = data.get("customFacets", {})
        custom_state = data.get("customState", {})
        ttl_definitions = data.get("ttlDefinitions")

        # Validate and handle different possible structures from LLM response
        if not isinstance(custom_facets, dict):
            error_msg = f"Invalid customFacets structure on attempt {current_attempts + 1}: expected dict, got {type(custom_facets).__name__}"
            print(f"[ERROR] [Custom Facet] {error_msg}")
            new_errors = custom_errors + [error_msg]
            return {
                "customFacetAttempts": current_attempts + 1,
                "customFacetErrors": new_errors,
                "messages": [HumanMessage(content=error_msg, name="custom_facet_agent")],
            }

        print(
            f"[INFO] [Custom Facet] Analysis complete. Created {len(custom_facets.get('facetDefinitions', {}))} custom facets.")

        # Prepare the update dictionary
        update_payload = {
            "customFacets": custom_facets,
            "customState": custom_state,
            "customFacetAttempts": current_attempts + 1,
            "messages": [HumanMessage(content=f"Applied independent reasoning - created {len(custom_facets.get('facetDefinitions', {}))} custom facets.", name="custom_facet_agent")],
        }

        # Add ttlDefinitions to the state if it was generated
        if ttl_definitions:
            update_payload["ttlDefinitions"] = ttl_definitions
            print(f"[INFO] [Custom Facet] TTL definitions generated ({len(ttl_definitions)} chars).")

        return update_payload

    except Exception as e:
        error_msg = f"Processing failed on attempt {current_attempts + 1}: {str(e)}"
        print(f"[ERROR] [Custom Facet] {error_msg}")

        new_errors = custom_errors + [error_msg]

        return {
            "customFacetAttempts": current_attempts + 1,
            "customFacetErrors": new_errors,
            "messages": [HumanMessage(content=error_msg, name="custom_facet_agent")],
        }

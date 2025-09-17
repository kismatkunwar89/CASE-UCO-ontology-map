import json
import re
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command

# --- Custom Module Imports ---
from state import State
from config import MAX_CUSTOM_FACET_ATTEMPTS, CUSTOM_FACET_AGENT_PROMPT

# =============================================================================
# Agent Setup
# =============================================================================

custom_facet_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# =============================================================================
# Agent Node Function
# =============================================================================


def custom_facet_node(state: State) -> Command:
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
        return Command(
            update={
                "customFacets": {},
                "customState": {
                    "reasoning": f"Max attempts ({MAX_CUSTOM_FACET_ATTEMPTS}) reached",
                    "errors": custom_errors
                },
                "customFacetAttempts": current_attempts
            },
            goto="supervisor"
        )

    if state.get("customFacets") is not None and not custom_errors:
        print("[INFO] [Custom Facet] Step already complete, skipping.")
        return Command(goto="supervisor")

    messages = state.get("messages", [])
    original_input = str(messages[0].content) if messages else ""
    ontology_map = state.get("ontologyMap", {})

    print("[INFO] [Custom Facet] Starting independent reasoning analysis...")

    error_feedback = ""
    if custom_errors:
        error_feedback = f"\n\nPREVIOUS ERRORS TO CONSIDER:\n" + \
            "\n".join(custom_errors[-2:])

    prompt = f"""
ORIGINAL USER INPUT:
{original_input}

STANDARD ONTOLOGY KEYS FROM AGENT 1:
{json.dumps(ontology_map, indent=2)}
{error_feedback}

Analyze the original user input independently and determine what custom facets are needed.
Compare with the standard ontology mapping and use your reasoning to create appropriate custom structures.
If no custom facets are needed, return empty JSON structures for "customFacets" and "customState".
"""

    print("[INFO] [Custom Facet] Sending prompt to LLM for analysis...")

    try:
        response = custom_facet_llm.invoke([
            {"role": "system", "content": CUSTOM_FACET_AGENT_PROMPT},
            {"role": "user", "content": prompt}
        ])

        print("[INFO] [Custom Facet] Received LLM response.")

        json_content = ""
        m = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", response.content, re.DOTALL)
        if m:
            json_content = m.group(1)
        else:
            json_content = response.content

        data = json.loads(json_content)
        custom_facets = data.get("customFacets", {})
        custom_state = data.get("customState", {})

        total_custom_props = sum(len(facet.get('properties', {}))
                                 for facet in custom_facets.values())
        print(
            f"[INFO] [Custom Facet] Analysis complete. Created {len(custom_facets)} custom facets.")

        return Command(
            update={
                "customFacets": custom_facets,
                "customState": custom_state,
                "customFacetAttempts": current_attempts + 1,
                "messages": [HumanMessage(content=f"Applied independent reasoning - created {len(custom_facets)} custom facets.", name="custom_facet_agent")],
            },
            goto="supervisor",
        )

    except Exception as e:
        error_msg = f"Processing failed on attempt {current_attempts + 1}: {str(e)}"
        print(f"[ERROR] [Custom Facet] {error_msg}")

        new_errors = custom_errors + [error_msg]

        return Command(
            update={
                "customFacetAttempts": current_attempts + 1,
                "customFacetErrors": new_errors,
                "messages": [HumanMessage(content=error_msg, name="custom_facet_agent")],
            },
            goto="supervisor",
        )

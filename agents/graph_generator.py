import json
import re
from typing import List

from langchain_core.messages import HumanMessage

# --- Custom Module Imports ---
from state import State
from config import (
    llm,
    MAX_GRAPH_GENERATOR_ATTEMPTS,
    GRAPH_GENERATOR_AGENT_PROMPT
)
from tools import generate_uuid
from utils import _get_input_artifacts
from agents.hallucination_checker import FeedbackProcessingAgent, DynamicCorrectionAgent

def format_hallucination_instructions(recent_feedbacks: List[str]) -> str:
    """Formats recent hallucination feedback into a detailed prompt section."""
    if not recent_feedbacks:
        return ""
    instructions = "## CRITICAL HALLUCINATION CORRECTIONS REQUIRED\n\n"
    for i, feedback in enumerate(recent_feedbacks, 1):
        instructions += f"### Correction {i}:\n{feedback}\n\n"
    instructions += """## MANDATORY RULES FOR THIS GENERATION:
1. ONLY use data that exists in the original input artifacts.
2. DO NOT add timestamps unless explicitly provided in input.
3. DO NOT fabricate IP addresses, ports, or hostnames.
4. Omit properties if the data is not in the input; do not invent values.
5. Double-check every value against the original input.\n\nFAILURE TO FOLLOW THESE RULES WILL RESULT IN ANOTHER HALLUCINATION FAILURE.
"""
    return instructions

def graph_generator_node(state: State) -> dict:
    """
    Generates the main JSON-LD graph by combining ontology and custom facet data.
    """
    current_attempts = state.get("graphGeneratorAttempts", 0)
    graph_errors = state.get("graphGeneratorErrors", [])

    print(f"[INFO] [Graph Generator] Attempt {current_attempts + 1}/{MAX_GRAPH_GENERATOR_ATTEMPTS}")

    if current_attempts >= MAX_GRAPH_GENERATOR_ATTEMPTS:
        print(f"[WARNING] [Graph Generator] Max attempts reached. Generating fallback response.")
        fallback_context = {}
        ontology_map = state.get("ontologyMap", {})
        if ontology_map and "context" in ontology_map:
            fallback_context = ontology_map["context"]
        else:
            fallback_context = {"kb": "http://example.org/kb/", "xsd": "http://www.w3.org/2001/XMLSchema#"}
        fallback_graph = {
            "@context": fallback_context,
            "@graph": [],
            "error": f"Graph generation failed after {MAX_GRAPH_GENERATOR_ATTEMPTS} attempts",
            "errors": graph_errors,
            "fallback": True
        }
        return {
            "jsonldGraph": fallback_graph,
            "graphGeneratorAttempts": current_attempts,
            "messages": [HumanMessage(content=f"Graph generation failed after {MAX_GRAPH_GENERATOR_ATTEMPTS} attempts, providing fallback", name="graph_generator_agent")]
        }

    ontology_map = state.get("ontologyMap", {})
    custom_facets = state.get("customFacets", {})
    custom_state = state.get("customState", {})
    ontology_markdown = state.get("ontologyMarkdown", "")
    validation_feedback = state.get("validation_feedback", "")
    validation_history = state.get("validationHistory", [])
    learning_context = state.get("learningContext", "")
    memory_context = state.get("memory_context", "")
    layer2_feedback_history = state.get("layer2_feedback_history", [])

    error_feedback = ""
    if graph_errors:
        error_feedback = f"\n\nPREVIOUS ERRORS TO CONSIDER:\n{chr(10).join(graph_errors[-2:])}\n\nPlease fix these issues in your JSON-LD generation."

    dynamic_instructions = format_hallucination_instructions(layer2_feedback_history)

    prompt = f"""
## STANDARD ONTOLOGY KEYS (from Agent 1):
{json.dumps(ontology_map, indent=2)}

## CUSTOM FACETS (from Agent 2):
{json.dumps(custom_facets, indent=2)}

## CUSTOM STATE:
{json.dumps(custom_state, indent=2)}

## ONTOLOGY RESEARCH CONTEXT (FULL markdown from Agent 1):
{ontology_markdown}

## VALIDATION FEEDBACK FOR CORRECTION:
{validation_feedback}

{error_feedback}

{dynamic_instructions}

## INSTRUCTIONS:
Combine the standard ontology mapping with the custom facets into a unified JSON-LD structure.
... (instructions as before) ...
"""

    try:
        graph_generator_llm = llm.bind_tools([generate_uuid])
        system_content = GRAPH_GENERATOR_AGENT_PROMPT
        response = graph_generator_llm.invoke([
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ])

        if response.tool_calls:
            uuids = {tool_call["id"]: generate_uuid.invoke(tool_call["args"]) for tool_call in response.tool_calls}
            uuid_instructions = f'''Use these UUIDs: {json.dumps(uuids, indent=2)}'''
            final_response = llm.invoke([
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
                response,
                {"role": "tool", "content": uuid_instructions}
            ])
            graph_out = final_response.content
        else:
            graph_out = response.content

        json_obj = None
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", graph_out, re.DOTALL)
        if m:
            json_content = m.group(1).strip()
        else:
            json_content = graph_out.strip()

        if not json_content:
            raise ValueError("Empty JSON content received from LLM")

        json_obj = json.loads(json_content)

        if "@context" not in json_obj or "@graph" not in json_obj:
            raise ValueError("Invalid JSON-LD structure: missing @context or @graph")

        if layer2_feedback_history:
            correction_agent = DynamicCorrectionAgent(llm)
            original_input = _get_input_artifacts(state)
            for feedback in layer2_feedback_history:
                json_obj = correction_agent.apply_corrections(json_obj, feedback, original_input)

        print(f"[SUCCESS] [Graph Generator] Successfully generated JSON-LD with {len(json_obj.get('@graph', []))} entities")

        return {
            "jsonldGraph": json_obj,
            "graphGeneratorAttempts": current_attempts + 1,
            "messages": [HumanMessage(content=json.dumps(json_obj, indent=2), name="graph_generator_agent")]
        }

    except Exception as e:
        error_msg = f"Processing failed on attempt {current_attempts + 1}: {str(e)}"
        print(f"[ERROR] [Graph Generator] {error_msg}")
        return {
            "graphGeneratorAttempts": current_attempts + 1,
            "graphGeneratorErrors": graph_errors + [error_msg],
        }

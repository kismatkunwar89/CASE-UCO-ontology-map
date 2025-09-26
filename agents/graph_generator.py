import json
import re
from typing import Any, List

from langchain_core.messages import HumanMessage

# --- Custom Module Imports ---
from state import State
from config import (
    llm,
    MAX_GRAPH_GENERATOR_ATTEMPTS,
    GRAPH_GENERATOR_AGENT_PROMPT
)
# Removed generate_uuid import - using deterministic UUID plan instead
from utils import _get_input_artifacts
from agents.hallucination_checker import FeedbackProcessingAgent, DynamicCorrectionAgent


def _normalise_value(value: Any) -> Any:
    if isinstance(value, dict):
        if "@value" in value:
            return value["@value"]
        if set(value.keys()) == {"@id"}:
            return value["@id"]
        return json.dumps(value, sort_keys=True)
    if isinstance(value, list):
        return tuple(_normalise_value(v) for v in value)
    return value


# Removed strict validation functions - LLM now has full control over graph generation

def _merge_llm_output_into_skeleton(skeleton_graph, llm_graph):
    """
    Merges properties from the LLM's graph into the skeleton graph.
    This ensures that no nodes are lost and that @id and @type are preserved.
    """
    skeleton_nodes_by_id = {node["@id"]: node for node in skeleton_graph.get("@graph", [])}
    
    for llm_node in llm_graph.get("@graph", []):
        node_id = llm_node.get("@id")
        if node_id in skeleton_nodes_by_id:
            # Copy all properties from llm_node except @id and @type
            for key, value in llm_node.items():
                if key not in ["@id", "@type"]:
                    skeleton_nodes_by_id[node_id][key] = value
    
    # The skeleton_graph is modified in place, but we return it for clarity
    return skeleton_graph


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

    print(
        f"[INFO] [Graph Generator] Attempt {current_attempts + 1}/{MAX_GRAPH_GENERATOR_ATTEMPTS}")

    if current_attempts >= MAX_GRAPH_GENERATOR_ATTEMPTS:
        print(
            f"[WARNING] [Graph Generator] Max attempts reached. Generating fallback response.")
        fallback_context = {}
        ontology_map = state.get("ontologyMap", {})
        if ontology_map and "context" in ontology_map:
            fallback_context = ontology_map["context"]
        else:
            fallback_context = {"kb": "http://example.org/kb/",
                                "xsd": "http://www.w3.org/2001/XMLSchema#"}
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
    source_properties = state.get("sourcePropertyMap", {})
    if not source_properties:
        print("[WARNING] [Graph Generator] No sourcePropertyMap provided; generator may lack real values.")
    custom_state = state.get("customState", {})
    ontology_markdown = state.get("ontologyMarkdown", "")
    validation_feedback = state.get("validation_feedback", "")
    validation_history = state.get("validationHistory", [])
    learning_context = state.get("learningContext", "")
    memory_context = state.get("memory_context", "")
    layer2_feedback_history = state.get("layer2_feedback_history", [])
    uuid_plan = state.get("uuidPlan", [])
    slot_type_map = state.get("slotTypeMap", {})

    # --- Build Skeleton Graph ---
    print("[INFO] [Graph Generator] Building skeleton graph from plan...")
    skeleton_graph = {"@graph": []}
    nodes_by_id = {}
    if uuid_plan and slot_type_map:
        included_records = []
        for record_plan in uuid_plan:
            primary_slug = None
            for slot_slug in record_plan.keys():
                lower_slug = slot_slug.lower()
                if "facet" in lower_slug or "relationship" in lower_slug:
                    continue
                primary_slug = slot_slug
                break
            if primary_slug is None and record_plan:
                primary_slug = next(iter(record_plan))
            included_slots = []
            for slot_slug, slot_uuid in record_plan.items():
                slot_type = slot_type_map.get(slot_uuid, "uco-core:UcoObject")
                include_slot = True
                if slot_slug != primary_slug:
                    lower_slug = slot_slug.lower()
                    payload = source_properties.get(slot_uuid, {}) if isinstance(source_properties, dict) else {}
                    slot_type_lower = slot_type.lower() if isinstance(slot_type, str) else ""
                    if "relationship" in lower_slug or slot_type_lower.endswith("relationship"):
                        include_slot = bool(payload.get("properties") or payload.get("raw"))
                    elif "facet" in lower_slug:
                        include_slot = bool(payload.get("properties") or payload.get("raw"))
                if not include_slot:
                    continue
                node = {
                    "@id": slot_uuid,
                    "@type": slot_type
                }
                skeleton_graph["@graph"].append(node)
                nodes_by_id[slot_uuid] = node
                included_slots.append((slot_slug, slot_uuid))
            included_records.append((primary_slug, included_slots))

        for primary_slug, slots in included_records:
            primary_uuid = None
            facet_refs = []
            for slot_slug, slot_uuid in slots:
                lower_slug = slot_slug.lower()
                if slot_slug == primary_slug:
                    primary_uuid = slot_uuid
                elif "facet" in lower_slug:
                    facet_refs.append({"@id": slot_uuid})
            if primary_uuid and facet_refs:
                parent_node = nodes_by_id.get(primary_uuid)
                if parent_node:
                    parent_node["uco-core:hasFacet"] = facet_refs

    error_feedback = ""
    if graph_errors:
        error_feedback = f"\n\nPREVIOUS ERRORS TO CONSIDER:\n{chr(10).join(graph_errors[-2:])}\n\nPlease fix these issues in your JSON-LD generation."

    dynamic_instructions = format_hallucination_instructions(
        layer2_feedback_history)

    prompt = f"""
## GRAPH SKELETON (Your starting point):
Your task is to fill in the properties for each entity in this pre-built graph skeleton based on the other information provided.
Do NOT add new entities. Do NOT change the @id or @type of existing entities.
```json
{json.dumps(skeleton_graph, indent=2)}
```

## STANDARD ONTOLOGY KEYS (from Agent 1):
{json.dumps(ontology_map, indent=2)}

   ## CUSTOM FACETS (from Agent 2):
   {json.dumps(custom_facets, indent=2)}

   ## SOURCE PROPERTY MAP (directly from evidence fields):
   {json.dumps(source_properties, indent=2)}

## VALIDATION FEEDBACK FOR CORRECTION:
{validation_feedback}

{error_feedback}

{dynamic_instructions}

## INSTRUCTIONS:
1.  Review the source data (in the ontology and custom facet maps).
   2.  For each entity in the GRAPH SKELETON, add the relevant properties and values, pulling data from SOURCE PROPERTY MAP when present.
3.  Return the completed JSON-LD graph.

## CRITICAL REMINDER ON PROPERTY PLACEMENT:
- The MOST IMPORTANT rule is the separation of object and facet properties.
- A property like `uco-observable:filePath` or `uco-observable:createdTime` MUST NOT appear on a `uco-observable:File` node.
- These properties MUST be placed on the corresponding facet node (e.g., `uco-observable:FileFacet`).
- The parent `File` node should ONLY contain the `uco-core:hasFacet` property pointing to its facets.
   - VIOLATING THIS RULE WILL CAUSE IMMEDIATE SYSTEM FAILURE. Double-check every property's location before outputting the graph.

   ## CRITICAL DATA INTEGRITY RULE:
   - You MUST NOT invent property values. Only use literals provided in SOURCE PROPERTY MAP or CUSTOM FACETS. If a value is absent, omit the property.
"""

    try:
        # Use standard LLM without tool binding since we have deterministic UUIDs
        system_content = GRAPH_GENERATOR_AGENT_PROMPT
        response = llm.invoke([
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ])

        graph_out = response.content

        json_obj = None
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", graph_out, re.DOTALL)
        if m:
            json_content = m.group(1).strip()
        else:
            json_content = graph_out.strip()

        if not json_content:
            raise ValueError("Empty JSON content received from LLM")

        llm_json_obj = json.loads(json_content)

        # Merge the LLM's output into our skeleton to preserve all nodes
        json_obj = _merge_llm_output_into_skeleton(skeleton_graph, llm_json_obj)

        # Ensure the context is present in the final graph
        if "@context" not in json_obj:
            json_obj["@context"] = {
                "case-investigation": "https://ontology.caseontology.org/case/investigation/",
                "kb": "http://example.org/kb/",
                "drafting": "http://example.org/ontology/drafting/",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "uco-action": "https://ontology.unifiedcyberontology.org/uco/action/",
                "core": "https://ontology.unifiedcyberontology.org/uco/core/",
                "identity": "https://ontology.unifiedcyberontology.org/uco/identity/",
                "location": "https://ontology.unifiedcyberontology.org/uco/location/",
                "observable": "https://ontology.unifiedcyberontology.org/uco/observable/",
                "tool": "https://ontology.unifiedcyberontology.org/uco/tool/",
                "types": "https://ontology.unifiedcyberontology.org/uco/types/",
                "vocabulary": "https://ontology.unifiedcyberontology.org/uco/vocabulary/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "dfc-ext": "https://www.w3.org/dfc-ext/"
            }

        if "@context" not in json_obj or "@graph" not in json_obj:
            raise ValueError(
                "Invalid JSON-LD structure: missing @context or @graph")

        if layer2_feedback_history:
            correction_agent = DynamicCorrectionAgent(llm)
            original_input = _get_input_artifacts(state)
            for feedback in layer2_feedback_history:
                json_obj = correction_agent.apply_corrections(
                    json_obj, feedback, original_input)

        # Ensure the context is present in the final graph
        if "@context" not in json_obj:
            json_obj["@context"] = {
                "case-investigation": "https://ontology.caseontology.org/case/investigation/",
                "kb": "http://example.org/kb/",
                "drafting": "http://example.org/ontology/drafting/",
                "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                "uco-action": "https://ontology.unifiedcyberontology.org/uco/action/",
                "core": "https://ontology.unifiedcyberontology.org/uco/core/",
                "identity": "https://ontology.unifiedcyberontology.org/uco/identity/",
                "location": "https://ontology.unifiedcyberontology.org/uco/location/",
                "observable": "https://ontology.unifiedcyberontology.org/uco/observable/",
                "tool": "https://ontology.unifiedcyberontology.org/uco/tool/",
                "types": "https://ontology.unifiedcyberontology.org/uco/types/",
                "vocabulary": "https://ontology.unifiedcyberontology.org/uco/vocabulary/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "dfc-ext": "https://www.w3.org/dfc-ext/"
            }

        # Validation removed - let LLM have full control over graph generation
        # The LLM has all necessary context from ontology research, custom facets, and source data

        print(
            f"[SUCCESS] [Graph Generator] Successfully generated JSON-LD with {len(json_obj.get('@graph', []))} entities")

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


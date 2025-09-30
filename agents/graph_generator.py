import json
import re
from typing import Any, Dict, List

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


DEFAULT_CONTEXT = {
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

def _enforce_property_placement(graph: dict, ontology_map: dict) -> dict:
    """
    Programmatically enforces correct property placement by moving properties
    from parent objects to their appropriate facets based on the ontology map.
    """
    print("[INFO] [Graph Cleanup] Running _enforce_property_placement...")
    
    graph_nodes = graph.get("@graph", [])
    if not graph_nodes:
        return graph

    nodes_by_id = {node["@id"]: node for node in graph_nodes}
    
    # Create a map of {property_name: facet_type}
    prop_to_facet_map = {}
    if isinstance(ontology_map.get("properties"), dict):
        for owner, props in ontology_map["properties"].items():
            if owner.endswith("Facet"):
                for prop in props:
                    prop_to_facet_map[prop] = owner

    for node in graph_nodes:
        node_type = node.get("@type", "")
        if isinstance(node_type, str) and node_type.endswith("Facet"):
            continue

        properties_to_move = {}
        for prop, value in node.items():
            if prop in ["@id", "@type", "uco-core:hasFacet"]:
                continue
            
            prop_name = prop.split(":")[-1]
            if prop_name in prop_to_facet_map:
                properties_to_move[prop] = value
        
        if properties_to_move:
            print(f"[INFO] [Graph Cleanup] Found {len(properties_to_move)} misplaced properties on node {node.get('@id')}")
            
            facet_refs = node.get("uco-core:hasFacet", [])
            if not facet_refs:
                continue

            for prop, value in properties_to_move.items():
                prop_name = prop.split(":")[-1]
                target_facet_type = prop_to_facet_map.get(prop_name)
                
                target_facet_node = None
                for facet_ref in facet_refs:
                    facet_id = facet_ref.get("@id")
                    if facet_id in nodes_by_id:
                        facet_node = nodes_by_id[facet_id]
                        if facet_node.get("@type") == target_facet_type:
                            target_facet_node = facet_node
                            break
                
                if target_facet_node is not None:
                    target_facet_node[prop] = value
                    del node[prop]
                    print(f"[INFO] [Graph Cleanup] Moved '{prop}' to facet {target_facet_node.get('@id')}")
                else:
                    print(f"[WARNING] [Graph Cleanup] Could not find a suitable facet for property '{prop}'")

    return graph

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


def _assign_properties(node: Dict[str, Any], properties: Dict[str, Any]) -> None:
    for prop, value in (properties or {}).items():
        # Skip None values and empty strings
        if value is None or value == "":
            continue
        node[prop] = value


def _slugify(name: str) -> str:
    return name.replace(" ", "_").replace("-", "_").lower()


def _build_deterministic_graph(
    skeleton_graph: Dict[str, Any],
    uuid_plan: List[Dict[str, str]],
    source_property_map: Dict[str, Dict[str, Any]],
    custom_facets: Dict[str, Any],
) -> Dict[str, Any]:
    nodes_by_id = {node["@id"]: node for node in skeleton_graph.get("@graph", [])}

    # Apply ontology-mapped properties
    for node_id, mapping in (source_property_map or {}).items():
        node = nodes_by_id.get(node_id)
        if not node:
            continue
        _assign_properties(node, mapping.get("properties") or {})

    # Map facet name to UUID using slug lookup
    slug_to_uuid: Dict[str, str] = {}
    for plan_row in uuid_plan or []:
        for slug, slot_uuid in plan_row.items():
            slug_to_uuid[slug] = slot_uuid

    for assignment in custom_facets.get("facetAssignments", []) or []:
        facet_name = assignment.get("facet")
        if not facet_name:
            continue
        facet_uuid = slug_to_uuid.get(_slugify(facet_name))
        if not facet_uuid:
            continue
        node = nodes_by_id.get(facet_uuid)
        if not node:
            continue
        values = assignment.get("values", {})
        filtered_values = {k: v for k, v in values.items() if v is not None}
        if filtered_values:
            _assign_properties(node, filtered_values)

    # Prune empty facet nodes
    filtered_nodes: List[Dict[str, Any]] = []
    empty_facets = set()
    for node in skeleton_graph.get("@graph", []):
        node_type = node.get("@type", "")
        if isinstance(node_type, str) and node_type.lower().endswith("facet"):
            has_payload = any(key not in ("@id", "@type", "uco-core:hasFacet") for key in node)
            if not has_payload:
                empty_facets.add(node.get("@id"))
                continue
        filtered_nodes.append(node)

    if empty_facets:
        for node in filtered_nodes:
            facets = node.get("uco-core:hasFacet")
            if facets:
                node["uco-core:hasFacet"] = [ref for ref in facets if ref.get("@id") not in empty_facets]

    return {"@context": DEFAULT_CONTEXT, "@graph": filtered_nodes}


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
                        include_slot = True
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

    json_obj = None
    used_llm = False
    try:
        print("[INFO] [Graph Generator] Attempting deterministic composition...")
        json_obj = _build_deterministic_graph(skeleton_graph, uuid_plan, source_properties, custom_facets)
        print(
            f"[SUCCESS] [Graph Generator] Deterministic JSON-LD generated with {len(json_obj.get('@graph', []))} entities")
    except Exception as det_exc:
        print(f"[WARNING] [Graph Generator] Deterministic composition failed: {det_exc}. Falling back to LLM.")
        json_obj = None

    if json_obj is None:
        error_feedback = ""
        if graph_errors:
            error_feedback = f"\n\nPREVIOUS ERRORS TO CONSIDER:\n{chr(10).join(graph_errors[-2:])}\n\nPlease fix these issues in your JSON-LD generation."

        dynamic_instructions = format_hallucination_instructions(layer2_feedback_history)

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
1. Review the source data and apply every property exactly where indicated.
2. For each slot in the skeleton, copy the values from SOURCE PROPERTY MAP without renaming keys.
3. If a facet assignment is provided, add those properties verbatim to that facet node.
4. Return a single JSON object containing `@context` and `@graph`.
"""

        try:
            system_content = GRAPH_GENERATOR_AGENT_PROMPT
            response = llm.invoke([
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
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
            json_obj = _merge_llm_output_into_skeleton(skeleton_graph, llm_json_obj)

            if "@context" not in json_obj:
                json_obj["@context"] = DEFAULT_CONTEXT

            if "@context" not in json_obj or "@graph" not in json_obj:
                raise ValueError("Invalid JSON-LD structure: missing @context or @graph")

            print(
                f"[SUCCESS] [Graph Generator] Successfully generated JSON-LD with {len(json_obj.get('@graph', []))} entities")

            used_llm = True

        except Exception as e:
            error_msg = f"Processing failed on attempt {current_attempts + 1}: {e}"
            print(f"[ERROR] [Graph Generator] {error_msg}")
            return {
                "graphGeneratorAttempts": current_attempts + 1,
                "graphGeneratorErrors": graph_errors + [error_msg],
            }

    if layer2_feedback_history:
        correction_agent = DynamicCorrectionAgent(llm)
        original_input = _get_input_artifacts(state)
        for feedback in layer2_feedback_history:
            json_obj = correction_agent.apply_corrections(json_obj, feedback, original_input)

    if "@context" not in json_obj:
        json_obj["@context"] = DEFAULT_CONTEXT

    # Final cleanup step to enforce property placement
    try:
        json_obj = _enforce_property_placement(json_obj, ontology_map)
    except Exception as e:
        print(f"[WARNING] [Graph Cleanup] Failed to enforce property placement: {e}")

    return {
        "jsonldGraph": json_obj,
        "graphGeneratorAttempts": current_attempts + 1,
        "messages": [
            HumanMessage(
                content=(
                    "JSON-LD graph generated via deterministic mapper."
                    if not used_llm
                    else "JSON-LD graph generated via LLM fallback."
                ),
                name="graph_generator_agent",
            )
        ],
    }
import json
import re
from copy import deepcopy
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


_TTL_HEADER = """@prefix dfc-ext: <https://www.w3.org/dfc-ext/> .\n@prefix uco-core: <https://ontology.unifiedcyberontology.org/uco/core/> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"""


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


def _to_camel_case(name: str) -> str:
    tokens = re.split(r"[^A-Za-z0-9]+", name)
    if not tokens:
        return name
    first, *rest = tokens
    return first.lower() + "".join(token.capitalize() for token in rest)


def _infer_xsd_datatype(value: Any) -> str:
    if isinstance(value, bool):
        return "xsd:boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "xsd:integer"
    if isinstance(value, float):
        return "xsd:decimal"
    return "xsd:string"


def _auto_generate_custom_facets(
    unmapped_details: list,
    raw_input_payload: Dict[str, Any],
    ontology_map: Dict[str, Any]
) -> tuple[Dict[str, Any], Dict[str, Any], str, Dict[str, Any]]:
    """Create deterministic custom facet definitions when the LLM declines."""

    if not unmapped_details:
        return {}, {}, "", {}

    record = {}
    if isinstance(raw_input_payload, dict):
        record = raw_input_payload.get("record") if isinstance(raw_input_payload.get("record"), dict) else {}

    existing_facets = set(ontology_map.get("facets", []) or [])
    base_name = "AutoUnmappedFacet"
    facet_name = base_name
    suffix = 2
    while facet_name in existing_facets:
        facet_name = f"{base_name}{suffix}"
        suffix += 1

    properties: Dict[str, Dict[str, str]] = {}
    values: Dict[str, Any] = {}
    for detail in unmapped_details:
        field = detail.get("field")
        if not field:
            continue
        local_name = _to_camel_case(field)
        prop_name = f"dfc-ext:{local_name}"
        sample_value = detail.get("sampleValue")
        if sample_value is None and record:
            sample_value = record.get(field)

        datatype = _infer_xsd_datatype(sample_value)
        properties[prop_name] = {"dataType": datatype}
        if sample_value is not None:
            values[prop_name] = sample_value

    if not properties:
        return {}, {}, "", {}

    match_fields = {}
    for key in ("EntryNumber", "SequenceNumber", "FileName", "@id"):
        if record and key in record and record[key] not in (None, ""):
            match_fields[key] = record[key]
    if not match_fields and record:
        sample_key = next((k for k, v in record.items() if v not in (None, "")), None)
        if sample_key:
            match_fields[sample_key] = record[sample_key]

    custom_facets = {
        "facetDefinitions": {
            facet_name: {
                "namespace": "dfc-ext",
                "reasoning": "Automatically generated facet covering unmapped evidence fields.",
                "properties": properties
            }
        },
        "facetAssignments": [
            {
                "match": match_fields,
                "facet": facet_name,
                "values": values
            }
        ]
    }

    custom_state = {
        "customFacetsNeeded": True,
        "autoGenerated": True,
        "totalCustomFacets": 1,
        "unmappedElementCount": len(unmapped_details),
        "extensionNamespace": "dfc-ext",
        "reasoning": "Deterministically generated custom facet to preserve unmapped fields."
    }

    ttl_lines = [_TTL_HEADER, "", "# Auto-generated facet for unmapped evidence fields"]
    ttl_lines.append(
        f"dfc-ext:{facet_name}\n  a owl:Class ;\n  rdfs:subClassOf uco-core:Facet ;\n  rdfs:label \"{facet_name}\" ;\n  rdfs:comment \"Automatically generated facet capturing unmapped evidence fields.\" ."
    )
    for prop_name, meta in properties.items():
        local = prop_name.split(":", 1)[1]
        ttl_lines.append(
            f"\ndfc-ext:{local}\n  a owl:DatatypeProperty ;\n  rdfs:domain dfc-ext:{facet_name} ;\n  rdfs:range {meta['dataType']} ;\n  rdfs:label \"{local}\" ."
        )
    ttl_definitions = "\n".join(ttl_lines)

    ontology_updates = {
        "facet_name": facet_name,
        "properties": list(properties.keys())
    }

    return custom_facets, custom_state, ttl_definitions, ontology_updates

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
    raw_input_payload = state.get("rawInputJSON")
    if isinstance(raw_input_payload, (dict, list)):
        original_input = json.dumps(raw_input_payload, indent=2)
    elif raw_input_payload is not None:
        original_input = str(raw_input_payload)
    else:
        messages = state.get("messages", [])
        original_input = next((str(m.content) for m in messages if hasattr(m, 'type') and m.type == "human"), "")

    # --- FAST PATH OPTIMIZATION ---
    additional_details = ontology_map.get("additional_details") or {}
    reserved_fields = {"artifact_type", "description", "source"}
    raw_unmapped = additional_details.get("unmappedElements", [])
    unmapped_elements: list[str] = []
    for element in raw_unmapped:
        if isinstance(element, str):
            if element not in reserved_fields:
                unmapped_elements.append(element)
        elif isinstance(element, dict):
            name = element.get("field") or element.get("name")
            if name and name not in reserved_fields:
                unmapped_elements.append(name)
        else:
            unmapped_elements.append(str(element))

    raw_unmapped_details = additional_details.get("unmappedElementDetails") or []
    cleaned_unmapped_details = []
    for detail in raw_unmapped_details:
        if not isinstance(detail, dict):
            continue
        field_name = detail.get("field") or detail.get("name")
        if not field_name or field_name in reserved_fields:
            continue

        cleaned_detail = {"field": field_name}
        if "valueType" in detail:
            cleaned_detail["valueType"] = detail["valueType"]

        if "sampleValue" in detail:
            cleaned_detail["sampleValue"] = detail["sampleValue"]
        elif isinstance(raw_input_payload, dict):
            record = raw_input_payload.get("record")
            if isinstance(record, dict) and field_name in record:
                value = record[field_name]
                cleaned_detail["sampleValue"] = value
                cleaned_detail.setdefault("valueType", type(value).__name__)

        if detail.get("isTruncated"):
            cleaned_detail["isTruncated"] = True

        cleaned_unmapped_details.append(cleaned_detail)

    if not cleaned_unmapped_details and unmapped_elements and isinstance(raw_input_payload, dict):
        record = raw_input_payload.get("record")
        if isinstance(record, dict):
            for field_name in unmapped_elements:
                if field_name in record:
                    value = record[field_name]
                    cleaned_unmapped_details.append(
                        {
                            "field": field_name,
                            "sampleValue": value,
                            "valueType": type(value).__name__
                        }
                    )

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

    print(f"[INFO] [Custom Facet] Unmapped fields forwarded: {len(unmapped_elements)}")

    print("[INFO] [Custom Facet] Starting independent reasoning analysis...")

    error_feedback = ""
    if custom_errors:
        error_feedback = f"\n\nPREVIOUS ERRORS TO CONSIDER:\n" + "\n".join(custom_errors[-2:])

    # New, clearer prompt with distinct roles for each piece of information
    unmapped_names_json = json.dumps(unmapped_elements, indent=2)
    unmapped_details_json = json.dumps(cleaned_unmapped_details, indent=2) if cleaned_unmapped_details else "[]"

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

**UNMAPPED FIELD NAMES (Agent 1)**
```json
{unmapped_names_json}
```

**UNMAPPED FIELD DETAILS (auto-generated)**
```json
{unmapped_details_json}
```

**YOUR INSTRUCTIONS**
1. Review the `UNMAPPED FIELD NAMES` and `UNMAPPED FIELD DETAILS` sections above.
2. If the names list is empty, your job is done. Return an empty `customFacets` object.
3. If the list is NOT empty, use the "ORIGINAL USER INPUT" to understand the context of each unmapped element and create custom facets for them.
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

        custom_facets = data.get("customFacets") or {}
        custom_state = data.get("customState") or {}
        ttl_definitions = data.get("ttlDefinitions")

        auto_facets = False
        if (not custom_facets.get("facetDefinitions") and cleaned_unmapped_details):
            generated_facets, generated_state, generated_ttl, ontology_updates = _auto_generate_custom_facets(
                cleaned_unmapped_details,
                raw_input_payload if isinstance(raw_input_payload, dict) else {},
                ontology_map,
            )
            if generated_facets:
                print("[INFO] [Custom Facet] Auto-generating deterministic custom facets for unmapped fields.")
                custom_facets = generated_facets
                custom_state = generated_state
                ttl_definitions = generated_ttl
                auto_facets = True

                facet_name = ontology_updates.get("facet_name")
                facet_props = ontology_updates.get("properties", [])
                updated_ontology_map = deepcopy(ontology_map)
                facets_list = list(updated_ontology_map.get("facets", []))
                if facet_name and facet_name not in facets_list:
                    facets_list.append(facet_name)
                    updated_ontology_map["facets"] = facets_list
                if facet_name and facet_props:
                    properties_map = updated_ontology_map.setdefault("properties", {})
                    existing_props = properties_map.get(facet_name, [])
                    if not existing_props:
                        properties_map[facet_name] = list(facet_props)
                    else:
                        for prop in facet_props:
                            if prop not in existing_props:
                                existing_props.append(prop)
                ontology_map = updated_ontology_map

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

        if auto_facets:
            update_payload["ontologyMap"] = ontology_map

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

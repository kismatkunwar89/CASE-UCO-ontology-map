import json
import re
from typing import Dict
from langchain_core.messages import HumanMessage
from config import llm
from state import State
from schemas import OntologyAnalysis
from utils import _get_input_artifacts

# =============================================================================
# Agent Setup
# =============================================================================

# This is the most reliable way to get structured JSON output.
# We bind the Pydantic model 'OntologyAnalysis' to the LLM, forcing it
# to return a JSON object that conforms to that schema.
structured_llm = llm.with_structured_output(OntologyAnalysis)


_FIELD_REFERENCE_PATTERN = re.compile(
    r"record(?:\[['\"]([A-Za-z0-9_]+)['\"]\]|\.([A-Za-z0-9_]+))"
)

_TABLE_ROW_PATTERN = re.compile(r"^\|")
_TABLE_HEADER_PATTERN = re.compile(r"^\|\s*PROPERTY\s*\|")
_FIELD_PATH_PATTERN = re.compile(
    r'''record(?:\[(?:["'])([A-Za-z0-9_]+)(?:["'])\]|\.([A-Za-z0-9_]+))'''
)


def _extract_mapped_fields(ontology_markdown: str) -> set:
    """Return the set of record field names that appear in the markdown mapping tables."""
    if not ontology_markdown:
        return set()

    mapped_fields = set()
    for match in _FIELD_REFERENCE_PATTERN.finditer(ontology_markdown):
        field_name = match.group(1) or match.group(2)
        if field_name:
            mapped_fields.add(field_name)
    return mapped_fields


def _get_record_fields(raw_input: dict) -> set:
    """Extract the top-level record field names from the raw input payload."""
    if not isinstance(raw_input, dict):
        return set()
    record = raw_input.get("record", {})
    if isinstance(record, dict):
        return set(record.keys())
    return set()


def _derive_unmapped_elements(raw_input: dict, ontology_markdown: str) -> list:
    """Compute unmapped record fields by diffing against the markdown coverage."""
    record_fields = _get_record_fields(raw_input)
    if not record_fields:
        return []

    mapped_fields = _extract_mapped_fields(ontology_markdown)
    if not mapped_fields:
        return sorted(record_fields)

    unmapped = [field for field in record_fields if field not in mapped_fields]
    return sorted(unmapped)


def _build_unmapped_details(raw_input: dict, unmapped_elements: list) -> list:
    """Return a structured summary for each unmapped field with sample values."""

    if not unmapped_elements or not isinstance(raw_input, dict):
        return []

    record = raw_input.get("record") if isinstance(raw_input.get("record"), dict) else {}
    if not record:
        return []

    details = []
    for field in unmapped_elements:
        detail = {"field": field}
        if field in record:
            value = record[field]
            # Capture the raw value when JSON-serializable, otherwise convert to string
            if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                sample_value = value
            else:
                sample_value = str(value)

            if isinstance(sample_value, str) and len(sample_value) > 120:
                detail["sampleValue"] = sample_value[:117] + "..."
                detail["isTruncated"] = True
            else:
                detail["sampleValue"] = sample_value

            detail["valueType"] = type(value).__name__
        details.append(detail)

    return details


def _parse_property_mappings(ontology_markdown: str, ontology_map: dict) -> Dict[str, Dict[str, list]]:
    """Extract property to record-field mappings from markdown tables."""

    if not ontology_markdown:
        return {}

    text_lines = ontology_markdown.splitlines()
    capturing = False
    property_rows = []

    for line in text_lines:
        if _TABLE_HEADER_PATTERN.match(line):
            capturing = True
            continue
        if capturing:
            stripped = line.strip()
            if stripped.startswith("|---"):
                continue
            if not _TABLE_ROW_PATTERN.match(line):
                capturing = False
                continue
            cells = [cell.strip() for cell in line.strip().split("|")][1:-1]
            if len(cells) < 4:
                continue
            property_name = cells[0]
            maps_to = cells[3]
            if not maps_to or maps_to.lower() == "(none)":
                continue
            match = _FIELD_PATH_PATTERN.search(maps_to)
            if not match:
                continue
            field = match.group(1) or match.group(2)
            if not field:
                continue
            property_rows.append((property_name, field))

    if not property_rows:
        return {}

    inverse_owner_map: Dict[str, List[str]] = {}
    for owner, props in (ontology_map.get("properties") or {}).items():
        for prop in props:
            inverse_owner_map.setdefault(prop, []).append(owner)

    property_field_map: Dict[str, Dict[str, list]] = {}
    for property_name, field in property_rows:
        owners = inverse_owner_map.get(property_name) or []
        for owner in owners:
            property_field_map.setdefault(owner, {}).setdefault(property_name, []).append(field)

    return property_field_map


SYNTHESIS_PROMPT = """"Ontology Synthesizer — Markdown Pass-Through
================================================
You receive an ontology research markdown report. Your job is to extract the final JSON mapping exactly as described below—without inventing, dropping, or rearranging data.

Target schema
-------------
```json
{
  "artifacts": ["string"],
  "classes": ["string"],
  "facets": ["string"],
  "properties": {"NodeName": ["propertyName"]},
  "relationships": [{"type": "hasFacet", "source": "Class", "target": "Facet"}],
  "analysis": "string",
  "additional_details": {}
}
```
All keys are required. Use empty lists/objects/strings only when the report truly has no data for that section.

Workflow
--------
1. Locate the **last fenced JSON block** in the markdown. This block already represents the analyst’s intended output.
2. Parse it. If any keys are missing, add them with empty defaults (list/object/string). Do not delete existing keys.
3. Validate:
   - `artifacts`, `classes`, `facets` are arrays of strings.
   - `properties` is a dictionary where each value is an array of strings. Preserve every property name exactly as given. Never drop a property unless the source JSON is malformed.
   - `relationships` is an array of objects. Keep every relationship; if the array is missing, create it from the report’s `#### Relationship Patterns` section.
   - `analysis` is a short domain-neutral string (reuse the value from the JSON or the `Intelligent Ontology Modeling Analysis` section).
   - `additional_details` is an object (use `{}` when absent).
4. If the fenced JSON omitted `relationships` or left them empty but the report listed `Class -> hasFacet -> Facet` bullets, populate the array with those entries. Do not invent other edges.
5. Output the normalized JSON **exactly once**. Do not wrap it in markdown.

Hard Rules
----------
- Do not invent new classes, facets, properties, or relationships.
- Do not drop items that already exist in the fenced JSON or tables.
- Preserve original casing of ontology terms.
- Keep the output domain agnostic—no case-specific narratives or raw evidence values.
"""

# =============================================================================
# Agent Node Function
# =============================================================================


def ontology_synthesis_node(state: State) -> dict:
    """
    Takes the raw markdown report from the research step and uses a structured
    output LLM to convert it into the 'OntologyAnalysis' Pydantic model.
    This is the most reliable method for guaranteeing a valid JSON structure.
    """
    print("[INFO] [Ontology Synthesizer] Starting structured synthesis from markdown report...")

    ontology_markdown = state.get("ontologyMarkdown")
    if not ontology_markdown:
        error_msg = "No ontology markdown found in state to synthesize."
        print(f"[ERROR] [Ontology Synthesizer] {error_msg}")
        return {"ontologyMap": {"error": error_msg}}

    # The user's original input is also useful context for the synthesizer.
    original_input = _get_input_artifacts(state)

    prompt = f"""
**Original User Input (for context):**
```
{original_input}
```

**Ontology Research Report to Synthesize:**
```markdown
{ontology_markdown}
```
"""

    try:
        # Invoke the structured LLM to get the Pydantic object directly
        synthesis_result = structured_llm.invoke([
            HumanMessage(content=SYNTHESIS_PROMPT),
            HumanMessage(content=prompt)
        ])

        if not isinstance(synthesis_result, OntologyAnalysis):
            raise TypeError(
                f"Expected OntologyAnalysis, but got {type(synthesis_result)}")

        print(
            "[SUCCESS] [Ontology Synthesizer] Successfully synthesized structured ontology map.")

        ontology_map = synthesis_result.dict()

        raw_input_payload = state.get("rawInputJSON")
        if raw_input_payload is None:
            raw_input_payload = state.get("input_artifacts")
        if isinstance(raw_input_payload, str):
            try:
                raw_input_payload = json.loads(raw_input_payload)
            except json.JSONDecodeError:
                raw_input_payload = {}

        unmapped_elements = _derive_unmapped_elements(raw_input_payload, ontology_markdown)
        mapped_fields = _extract_mapped_fields(ontology_markdown)
        record_fields = _get_record_fields(raw_input_payload)
        unmapped_details = _build_unmapped_details(raw_input_payload, unmapped_elements)
        property_field_map = _parse_property_mappings(ontology_markdown, ontology_map)

        additional_details = ontology_map.get("additional_details") or {}
        additional_details["unmappedElements"] = unmapped_elements
        if unmapped_details:
            additional_details["unmappedElementDetails"] = unmapped_details

        if record_fields:
            mapped_record_fields = sorted(field for field in record_fields if field in mapped_fields)
            coverage_stats = {
                "totalRecordFields": len(record_fields),
                "mappedRecordFieldCount": len(mapped_record_fields),
                "unmappedRecordFieldCount": len(unmapped_elements),
            }
            if mapped_record_fields:
                coverage_stats["mappedRecordFields"] = mapped_record_fields
        else:
            coverage_stats = {
                "totalRecordFields": 0,
                "mappedRecordFieldCount": 0,
                "unmappedRecordFieldCount": len(unmapped_elements),
            }

        additional_details["coverageStats"] = coverage_stats
        if property_field_map:
            additional_details["propertyFieldMap"] = property_field_map

        ontology_map["additional_details"] = additional_details

        return {"ontologyMap": ontology_map}

    except Exception as e:
        error_msg = f"Failed to synthesize ontology map: {e}"
        print(f"[ERROR] [Ontology Synthesizer] {error_msg}")
        return {"ontologyMap": {"error": error_msg}}

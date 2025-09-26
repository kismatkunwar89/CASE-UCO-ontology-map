

import json
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

        # The output of the structured LLM is already a Pydantic model,
        # so we can convert it to a dict for the state.
        # Use .dict() for Pydantic v1
        return {"ontologyMap": synthesis_result.dict()}

    except Exception as e:
        error_msg = f"Failed to synthesize ontology map: {e}"
        print(f"[ERROR] [Ontology Synthesizer] {error_msg}")
        return {"ontologyMap": {"error": error_msg}}

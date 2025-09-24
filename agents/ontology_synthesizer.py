

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

SYNTHESIS_PROMPT = """You are a data synthesis expert. Your task is to read the provided markdown report, which contains a detailed analysis of forensic artifacts mapped to the CASE/UCO ontology.

Based *only* on the information in the report, extract the data and structure it as a valid JSON object that conforms to the requested schema.

- The 'properties', 'relationships', and 'additional_details' fields are required. If there is no information for them in the report, you MUST populate them with empty values (e.g., {}, [], or a default note) rather than omitting them.
- Carefully extract all classes, facets, properties, and relationships mentioned.
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
             raise TypeError(f"Expected OntologyAnalysis, but got {type(synthesis_result)}")

        print("[SUCCESS] [Ontology Synthesizer] Successfully synthesized structured ontology map.")

        # The output of the structured LLM is already a Pydantic model,
        # so we can convert it to a dict for the state.
        return {"ontologyMap": synthesis_result.dict()} # Use .dict() for Pydantic v1

    except Exception as e:
        error_msg = f"Failed to synthesize ontology map: {e}"
        print(f"[ERROR] [Ontology Synthesizer] {error_msg}")
        return {"ontologyMap": {"error": error_msg}}

import json
import re
from typing import Literal, List

from langchain_core.messages import HumanMessage
from langgraph.types import Command


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

# =============================================================================
# Helper & Guardrail Functions
# =============================================================================


def apply_hallucination_corrections(jsonld_data: dict, feedback: str) -> dict:
    """Apply hallucination corrections using dynamic LLM-based agent."""
    # This function is deprecated - use DynamicCorrectionAgent instead
    # Keeping for backward compatibility but delegating to dynamic agent
    print("[INFO] Using dynamic LLM-based correction agent instead of hardcoded guardrails")

    # The actual correction is now handled by DynamicCorrectionAgent
    # which uses LLM reasoning to identify and remove fabricated fields
    # based on the specific feedback provided, not hardcoded rules

    return jsonld_data


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
5. Double-check every value against the original input.

FAILURE TO FOLLOW THESE RULES WILL RESULT IN ANOTHER HALLUCINATION FAILURE.
"""
    return instructions

# =============================================================================
# Agent Node Function
# =============================================================================


def graph_generator_node(state: State) -> Command:
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

        # Generate dynamic fallback JSON-LD structure using available context
        # Extract context from state or use minimal fallback
        fallback_context = {}
        ontology_map = state.get("ontologyMap", {})
        if ontology_map and "context" in ontology_map:
            fallback_context = ontology_map["context"]
        else:
            # Minimal fallback context - no hardcoded values
            fallback_context = {
                "kb": "http://example.org/kb/",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            }

        fallback_graph = {
            "@context": fallback_context,
            "@graph": [],
            "error": f"Graph generation failed after {MAX_GRAPH_GENERATOR_ATTEMPTS} attempts",
            "errors": graph_errors,
            "fallback": True
        }

        return Command(
            update={
                "jsonldGraph": fallback_graph,
                "graphMarkdown": json.dumps(fallback_graph, indent=2),
                "graphGeneratorAttempts": current_attempts,
                "messages": [HumanMessage(content=f"Graph generation failed after {MAX_GRAPH_GENERATOR_ATTEMPTS} attempts, providing fallback", name="graph_generator_agent")],
            },
            goto="supervisor",
        )

    # --- Prepare Prompt Inputs (Enhanced like complete_main_code.py) ---
    ontology_map = state.get("ontologyMap", {})
    custom_facets = state.get("customFacets", {})
    custom_state = state.get("customState", {})
    ontology_markdown = state.get("ontologyMarkdown", "")
    validation_feedback = state.get("validation_feedback", "")
    validation_history = state.get("validationHistory", [])
    learning_context = state.get("learningContext", "")
    memory_context = state.get("memory_context", "")
    layer2_feedback_history = state.get("layer2_feedback_history", [])

    print("🏗️ [GRAPH GENERATOR] Combining ontology keys + custom facets + markdown context into JSON-LD")
    print(f"📄 [MARKDOWN VERIFICATION] Checking markdown context availability:")
    print(f"   ✓ Markdown received: {'YES' if ontology_markdown else 'NO'}")
    print(f"   ✓ Markdown length: {len(ontology_markdown)} characters")
    print(f"   ✓ Markdown type: {type(ontology_markdown)}")

    print(f"📦 [INPUT SUMMARY] Graph Generator inputs:")
    print(f"   • Ontology Map Keys: {list(ontology_map.keys())}")
    print(f"   • Custom Facets Count: {len(custom_facets)}")
    print(f"   • Custom State Available: {'YES' if custom_state else 'NO'}")

    # Enhanced error feedback
    error_feedback = ""
    if graph_errors:
        error_feedback = f"\n\nPREVIOUS ERRORS TO CONSIDER:\n{chr(10).join(graph_errors[-2:])}\n\nPlease fix these issues in your JSON-LD generation."

    # Learning section (validation) - like complete_main_code.py
    learning_section = ""
    if validation_history:
        learning_section = f"""
## LEARNING FROM PREVIOUS VALIDATION ATTEMPTS

You have made {len(validation_history)} previous validation attempts. Here's what you've learned:

### Previous Validation Results:
"""
        for i, attempt in enumerate(validation_history[-3:], 1):
            learning_section += f"""
**Attempt {attempt.get('attempt', i)}:**
- Conforms: {attempt.get('conforms', 'Unknown')}
- Violations: {attempt.get('violation_count', 0)}
- Warnings: {attempt.get('warning_count', 0)}
- Key Issues: {attempt.get('key_issues', 'None identified')}
- Feedback: {attempt.get('feedback', 'No feedback')[:200]}...
"""
        learning_section += f"""
### Key Learning Points:
{learning_context}

### Memory-Based Learning:
{memory_context if memory_context != "No previous memory available" else "No previous memory patterns available"}

### Instructions for This Attempt:
- Apply all lessons learned from previous attempts
- Focus on the specific issues identified in validation feedback
- Use the accumulated knowledge to avoid repeating the same mistakes
- Apply memory-based corrections to avoid previously identified failure patterns
- Build upon successful patterns from previous attempts
"""

    # Dynamic hallucination feedback processing
    dynamic_instructions = ""
    recent_feedbacks = [fb for fb in layer2_feedback_history[-2:]
                        if isinstance(fb, str) and fb.strip()]
    if recent_feedbacks:
        feedback_agent = FeedbackProcessingAgent(llm)
        print(
            "[INFO] [Graph Generator] Processing hallucination feedback with dynamic agent.")
        dynamic_instructions = feedback_agent.analyze_feedback(
            recent_feedbacks)

    # --- Build Enhanced Prompt (like complete_main_code.py) ---
    prompt = f"""
## STANDARD ONTOLOGY KEYS (from Agent 1):
{json.dumps(ontology_map, indent=2)}

## CUSTOM FACETS (from Agent 2):
{json.dumps(custom_facets, indent=2)}

## CUSTOM STATE:
{json.dumps(custom_state, indent=2)}

## ONTOLOGY RESEARCH CONTEXT (FULL markdown from Agent 1):
{ontology_markdown}

{learning_section}

## VALIDATION FEEDBACK FOR CORRECTION:
{validation_feedback}

{error_feedback}

## INSTRUCTIONS:
Combine the standard ontology mapping with the custom facets into a unified JSON-LD structure.
Use the detailed ontology research context to make informed decisions about property usage and relationships.
Integrate both standard and custom properties logically.
Generate valid JSON-LD even if custom facets are empty.

## CRITICAL JSON FORMATTING REQUIREMENTS:
- You MUST return ONLY valid JSON-LD
- NO explanatory text before or after the JSON
- NO markdown code blocks (```json```)
- Start with {{ and end with }}
- Use proper JSON syntax: quotes around all keys and string values
- NO trailing commas
- Use the 'generate_uuid' tool for ALL '@id' values

# If hallucination feedback is present in history, apply it precisely (remove fabricated fields, keep only input-grounded values)
{dynamic_instructions}
"""

    # Add previous output section like complete_main_code.py
    previous_output_section = state.get("graphMarkdown", "")
    prompt = f"""{prompt}

## PREVIOUS OUTPUT (if any):
{previous_output_section}
"""

    try:
        # --- LLM Invocation ---
        graph_generator_llm = llm.bind_tools([generate_uuid])
        system_content = GRAPH_GENERATOR_AGENT_PROMPT
        response = graph_generator_llm.invoke([
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ])

        # --- Enhanced Tool Call Handling (Fix for Duplicate UUIDs) ---
        if response.tool_calls:
            uuids = {}
            uuid_counter = {}  # Track how many UUIDs of each type we've generated

            for tool_call in response.tool_calls:
                if tool_call["name"] == "generate_uuid":
                    entity_type = tool_call["args"].get(
                        'entity_type', 'entity')

                    # Generate unique UUID for each call, even if same entity_type
                    uuid_result = generate_uuid.invoke(tool_call["args"])

                    # Create unique key for each UUID call
                    if entity_type not in uuid_counter:
                        uuid_counter[entity_type] = 0
                    uuid_counter[entity_type] += 1

                    # Store with unique key to prevent overwriting
                    unique_key = f"{entity_type}_{uuid_counter[entity_type]}"
                    uuids[unique_key] = uuid_result

                    print(
                        f"[DEBUG] Generated UUID for {unique_key}: {uuid_result}")

            # Enhanced prompt to handle multiple UUIDs of same type
            uuid_instructions = f"""
Use these UUIDs in your JSON-LD generation. Each UUID is unique - do not reuse any UUID:

{json.dumps(uuids, indent=2)}

CRITICAL INSTRUCTIONS:
- Each UUID can only be used ONCE in the entire JSON-LD
- If you have multiple entities of the same type, use different UUIDs
- Map UUIDs to @id fields as follows:
  - For first entity of type 'relationship': use relationship_1 UUID
  - For second entity of type 'relationship': use relationship_2 UUID
  - And so on for any entity type
- NEVER reuse the same UUID for different entities
"""

            final_response = llm.invoke([
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": uuid_instructions}
            ])
            graph_out = final_response.content
        else:
            graph_out = response.content

        # --- Enhanced Response Parsing and Correction ---
        try:
            # Try multiple parsing strategies
            json_obj = None

            # Strategy 1: Look for fenced JSON blocks
            m = re.search(
                r"```(?:json)?\s*(\{.*?\})\s*```", graph_out, re.DOTALL)
            if m:
                json_content = m.group(1).strip()
                print(
                    f"[DEBUG] [Graph Generator] Extracted fenced JSON: {len(json_content)} chars")
            else:
                # Strategy 2: Look for JSON-like content starting with {
                json_match = re.search(r'\{.*\}', graph_out, re.DOTALL)
                if json_match:
                    json_content = json_match.group(0).strip()
                    print(
                        f"[DEBUG] [Graph Generator] Extracted JSON pattern: {len(json_content)} chars")
                else:
                    # Strategy 3: Use raw response
                    json_content = graph_out.strip()
                    print(
                        f"[DEBUG] [Graph Generator] Using raw response: {len(json_content)} chars")

            if not json_content:
                raise ValueError("Empty JSON content received from LLM")

            # Try to parse the JSON
            try:
                json_obj = json.loads(json_content)
            except json.JSONDecodeError as json_err:
                # Strategy 4: Try to fix common JSON issues
                print(
                    f"[DEBUG] [Graph Generator] Initial JSON parse failed: {json_err}")

                # Fix common issues
                fixed_json = json_content

                # Fix trailing commas
                fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)

                # Fix missing quotes around keys (but not values)
                fixed_json = re.sub(r'(\w+):', r'"\1":', fixed_json)

                # Try parsing again
                try:
                    json_obj = json.loads(fixed_json)
                    print(
                        f"[DEBUG] [Graph Generator] JSON fixed and parsed successfully")
                except json.JSONDecodeError as fix_err:
                    print(
                        f"[DEBUG] [Graph Generator] JSON fix failed: {fix_err}")
                    raise json_err  # Raise original error

            # Validate JSON-LD structure
            if "@context" not in json_obj or "@graph" not in json_obj:
                raise ValueError(
                    "Invalid JSON-LD structure: missing @context or @graph")

        except json.JSONDecodeError as e:
            error_msg = f"JSON parsing failed on attempt {current_attempts + 1}: {str(e)}"
            print(f"[ERROR] [Graph Generator] {error_msg}")
            print(
                f"[DEBUG] [Graph Generator] Raw response: {graph_out[:500]}...")
            new_errors = graph_errors + [error_msg]
            return Command(
                update={
                    "graphGeneratorAttempts": current_attempts + 1,
                    "graphGeneratorErrors": new_errors,
                },
                goto="supervisor",
            )
        except ValueError as e:
            error_msg = f"JSON-LD validation failed on attempt {current_attempts + 1}: {str(e)}"
            print(f"[ERROR] [Graph Generator] {error_msg}")
            new_errors = graph_errors + [error_msg]
            return Command(
                update={
                    "graphGeneratorAttempts": current_attempts + 1,
                    "graphGeneratorErrors": new_errors,
                },
                goto="supervisor",
            )

        if recent_feedbacks:
            print("[INFO] [Graph Generator] Applying dynamic corrections...")
            correction_agent = DynamicCorrectionAgent(llm)
            original_input = _get_input_artifacts(state)
            for feedback in recent_feedbacks:
                json_obj = correction_agent.apply_corrections(
                    json_obj, feedback, original_input)

        print(
            f"[SUCCESS] [Graph Generator] Successfully generated JSON-LD with {len(json_obj.get('@graph', []))} entities")

        # Enhanced learning context update like complete_main_code.py
        new_learning_context = f"""
Previous attempt {current_attempts + 1}:
- Generated {len(json_obj.get('@graph', []))} entities
- Used {len(ontology_map.get('classes', []))} standard classes
- Used {len(custom_facets)} custom facets
- Applied validation feedback: {'Yes' if validation_feedback else 'No'}
- Applied dynamic hallucination corrections: {'Yes' if bool(recent_feedbacks) else 'No'}
- Learning from {len(validation_history)} previous validation attempts
"""

        return Command(
            update={
                "jsonldGraph": json_obj,
                "graphMarkdown": json.dumps(json_obj, indent=2),
                "graphGeneratorAttempts": current_attempts + 1,
                "learningContext": learning_context + new_learning_context,
                "messages": [HumanMessage(content=json.dumps(json_obj, indent=2), name="graph_generator_agent")],
                "validation_result": {},
                "validation_feedback": "",
            },
            goto="validator_node",
        )

    except Exception as e:
        error_msg = f"Processing failed on attempt {current_attempts + 1}: {str(e)}"
        print(f"[ERROR] [Graph Generator] {error_msg}")
        new_errors = graph_errors + [error_msg]
        return Command(
            update={
                "graphGeneratorAttempts": current_attempts + 1,
                "graphGeneratorErrors": new_errors,
            },
            goto="supervisor",
        )

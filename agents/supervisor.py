from typing import Literal
from langgraph.graph import END
from langgraph.types import Command

# Import from our custom files
from state import State
from schemas import Router
from memory import update_memory_context
from config import (
    llm,
    SUPERVISOR_AGENT_PROMPT,
    MAX_CUSTOM_FACET_ATTEMPTS,
    MAX_GRAPH_GENERATOR_ATTEMPTS,
    MAX_VALIDATION_ATTEMPTS
)


def supervisor_node(state: State) -> Command:
    """
    The central supervisor node that directs the workflow and integrates memory.
    """
    messages = [
        {"role": "system", "content": SUPERVISOR_AGENT_PROMPT}] + state["messages"]

    # The LLM decides the next step
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]

    print(f"🎯 [SUPERVISOR] LLM Decision: {goto}")

    # --- Memory Integration ---
    memory_context = update_memory_context(state)
    state["memory_context"] = memory_context
    if memory_context != "No previous memory available":
        print(f"🧠 [MEMORY] Context loaded: {len(memory_context)} characters")

    # --- State-based Routing Logic ---
    ontology_complete = bool(state.get("ontologyMap")
                             and state.get("ontologyMarkdown"))
    custom_facets_complete = bool(
        state.get("customFacets") is not None and state.get("customState") is not None)
    graph_complete = bool(state.get("jsonldGraph"))

    validation_result = state.get("validation_result", {})
    validation_complete = validation_result.get("is_clean", False)

    # Get attempt counters
    custom_attempts = state.get("customFacetAttempts", 0)
    graph_attempts = state.get("graphGeneratorAttempts", 0)
    validation_attempts = state.get("validationAttempts", 0)

    print(
        f"📊 [SUPERVISOR] State check: Ontology={ontology_complete}, CustomFacets={custom_facets_complete}, Graph={graph_complete}, Validation={validation_complete}")
    print(
        f"🔄 [SUPERVISOR] Attempts: CustomFacet={custom_attempts}/{MAX_CUSTOM_FACET_ATTEMPTS}, GraphGen={graph_attempts}/{MAX_GRAPH_GENERATOR_ATTEMPTS}, Validation={validation_attempts}/{MAX_VALIDATION_ATTEMPTS}")

    # Enhanced routing logic matching complete_main_code.py
    if goto == "FINISH":
        print("🏁 [SUPERVISOR] Task completed!")
        return Command(goto=END)
    elif goto == "ontology_research_node" and ontology_complete:
        print(
            "⚠️ [SUPERVISOR] Ontology already complete, redirecting to custom facet agent")
        return Command(goto="custom_facet_node")
    elif goto == "custom_facet_node":
        if custom_facets_complete and custom_attempts < MAX_CUSTOM_FACET_ATTEMPTS:
            print(
                "⚠️ [SUPERVISOR] Custom facets complete, redirecting to graph generator")
            return Command(goto="graph_generator_node")
        elif custom_attempts >= MAX_CUSTOM_FACET_ATTEMPTS:
            print(
                f"⚠️ [SUPERVISOR] Custom facet max attempts ({MAX_CUSTOM_FACET_ATTEMPTS}) reached, proceeding to graph generator")
            return Command(goto="graph_generator_node")
        elif not ontology_complete:
            print("⚠️ [SUPERVISOR] Need ontology research first, redirecting")
            return Command(goto="ontology_research_node")
    elif goto == "graph_generator_node":
        if graph_complete and validation_complete and graph_attempts < MAX_GRAPH_GENERATOR_ATTEMPTS:
            print("✅ [SUPERVISOR] Graph complete and validated, finishing")
            return Command(goto=END)
        elif graph_complete and not validation_complete:
            print(
                "🔄 [SUPERVISOR] Graph complete but validation failed, routing to validator")
            return Command(goto="validator_node")
        elif graph_attempts >= MAX_GRAPH_GENERATOR_ATTEMPTS:
            print(
                f"⚠️ [SUPERVISOR] Graph generator max attempts ({MAX_GRAPH_GENERATOR_ATTEMPTS}) reached, finishing with available data")
            return Command(goto=END)
        elif not custom_facets_complete and custom_attempts < MAX_CUSTOM_FACET_ATTEMPTS:
            print("⚠️ [SUPERVISOR] Need custom facets first, redirecting")
            return Command(goto="custom_facet_node")
    elif goto == "validator_node":
        # Check hallucination completion status
        hallucination_result = state.get("hallucination_result", {})
        hallucination_complete = hallucination_result.get(
            "validation_decision") == "PASS"
        hallucination_attempts = state.get("hallucinationAttempts", 0)

        # Check if validation failed and we have feedback to send back to graph generator
        validation_result = state.get("validation_result", {})
        validation_feedback = state.get("validation_feedback", "")

        if validation_complete and not hallucination_complete:
            print("🔄 [SUPERVISOR] Validation passed, routing to hallucination check")
            return Command(goto="hallucination_check_node")
        elif validation_complete and hallucination_complete:
            print("✅ [SUPERVISOR] All validation complete, finishing")
            return Command(goto=END)
        elif validation_attempts >= MAX_VALIDATION_ATTEMPTS:
            print("⚠️ [SUPERVISOR] Validation max attempts reached, finishing")
            return Command(goto=END)
        elif not graph_complete:
            print("⚠️ [SUPERVISOR] Need graph generation first, redirecting")
            return Command(goto="graph_generator_node")
        elif validation_feedback and not validation_result.get("is_clean", False):
            # KEY FIX: Send validation feedback back to graph generator for correction
            print(
                "🔄 [SUPERVISOR] Validation failed with feedback, routing to graph generator for correction")
            print(
                f"📝 [SUPERVISOR] Feedback to apply: {validation_feedback[:100]}...")
            return Command(goto="graph_generator_node")
        else:
            print("🔄 [SUPERVISOR] Routing to validator for validation")
            return Command(goto="validator_node")

    return Command(goto=goto)

from langgraph.graph import StateGraph, END, START
from typing import Literal

# --- Custom Module Imports ---
from state import State
from schemas import Router
from config import llm, SUPERVISOR_AGENT_PROMPT

# Import all agent nodes
from config import llm, SUPERVISOR_AGENT_PROMPT, MAX_GRAPH_GENERATOR_ATTEMPTS
from agents.supervisor import supervisor_node
from agents.ontology_researcher import ontology_research_step_node
from agents.ontology_synthesizer import ontology_synthesis_node
from agents.custom_facet import custom_facet_node
from agents.graph_generator import graph_generator_node
from agents.validator import validator_node
from agents.hallucination_checker import hallucination_check_node
from agents.uuid_planner import uuid_planner_node, invalidate_uuid_plan_node
# =============================================================================
# Routing Functions
# =============================================================================


from memory import update_memory_context
from config import (
    MAX_CUSTOM_FACET_ATTEMPTS,
    MAX_GRAPH_GENERATOR_ATTEMPTS,
    MAX_VALIDATION_ATTEMPTS
)


def route_supervisor(state: State) -> str:
    """
    The central supervisor router that directs the workflow and integrates memory.
    This function contains the primary routing logic for the agentic graph.
    """
    # Update memory context first
    memory_context = update_memory_context(state)
    state["memory_context"] = memory_context

    # --- NEW GUARDRAIL: Check for critical errors from previous steps ---
    if state.get("customFacetErrors") or state.get("graphGeneratorErrors") or "error" in state.get("ontologyMap", {}):
        print(
            "❌ [ROUTER] Critical error detected in a previous step. Terminating workflow.")
        return "__end__"

    # Get the latest message to understand the current context
    messages = state.get("messages", [])

    # Determine the next step based on the current state
    ontology_markdown_complete = bool(state.get("ontologyMarkdown"))
    ontology_map_complete = bool(state.get("ontologyMap"))
    custom_facets_complete = state.get("customFacets") is not None
    graph_complete = bool(state.get("jsonldGraph"))
    validation_complete = state.get(
        "validation_result", {}).get("is_clean", False)

    # Get attempt counters
    custom_attempts = state.get("customFacetAttempts", 0)
    graph_attempts = state.get("graphGeneratorAttempts", 0)
    validation_attempts = state.get("validationAttempts", 0)

    # --- Deterministic Routing Logic ---
    if not ontology_markdown_complete:
        print(
            "🎯 [ROUTER] State: Ontology markdown not found. -> ontology_research_step_node")
        return "ontology_research_step_node"

    if not ontology_map_complete:
        print("🎯 [ROUTER] State: Ontology map not found. -> ontology_synthesis_node")
        return "ontology_synthesis_node"

    if not custom_facets_complete:
        if custom_attempts < MAX_CUSTOM_FACET_ATTEMPTS:
            print(
                "🎯 [ROUTER] State: Custom facets not complete. -> custom_facet_node")
            return "custom_facet_node"
        else:
            print(
                "⚠️ [ROUTER] State: Max custom facet attempts reached. Proceeding without custom facets.")
            # Fall through to the next step even if custom facets fail

    # --- NEW: Route to UUID Planner if no plan exists ---
    if not state.get("uuidPlan"):
        print("🎯 [ROUTER] State: UUID plan not found. -> uuid_planner_node")
        return "uuid_planner_node"

    if not graph_complete:
        if graph_attempts < MAX_GRAPH_GENERATOR_ATTEMPTS:
            print("🎯 [ROUTER] State: Graph not complete. -> graph_generator_node")
            return "graph_generator_node"
        else:
            print(
                "⚠️ [ROUTER] State: Max graph generator attempts reached. -> validator_node")
            return "validator_node"

    if not validation_complete:
        if validation_attempts < MAX_VALIDATION_ATTEMPTS:
            # If graph is complete but validation failed, we might need to go back
            validation_feedback = state.get("validation_feedback", "")
            if validation_feedback:
                print(
                    "🎯 [ROUTER] State: Validation failed with feedback. -> graph_generator_node")
                return "graph_generator_node"
            else:
                print("🎯 [ROUTER] State: Graph not validated. -> validator_node")
                return "validator_node"
        else:
            print("⚠️ [ROUTER] State: Max validation attempts reached. -> __end__")
            return "__end__"

    # If all steps are complete, finish the workflow
    print("✅ [ROUTER] State: All steps complete. -> __end__")
    return "__end__"


def route_after_validation(state: State) -> Literal["hallucination_check_node", "graph_generator_node", "invalidate_uuid_plan_node", "__end__"]:
    """
    Determines the next step after the structural validation node runs.
    Routes to plan invalidation if an ID-related error is found.
    """
    validation_result = state.get("validation_result", {})
    is_clean = validation_result.get("is_clean", False)
    validation_attempts = state.get("validationAttempts", 0)

    if is_clean:
        return "hallucination_check_node"

    if validation_attempts >= MAX_VALIDATION_ATTEMPTS:
        print("[INFO] [Routing] Max validation attempts reached. Terminating.")
        return "__end__"

    # Intelligent routing based on feedback content
    feedback = state.get("validation_feedback", "").lower()
    id_error_keywords = ["@id", "uuid", "identifier", "reference"]
    if any(keyword in feedback for keyword in id_error_keywords):
        print(
            "🐞 [ROUTER] ID-related error detected. Routing to invalidate and regenerate UUID plan.")
        return "invalidate_uuid_plan_node"
    else:
        print(
            "🎯 [ROUTER] Non-ID validation error detected. Routing directly back to generator for correction.")
        return "graph_generator_node"


def route_after_hallucination_check(state: State) -> Literal["graph_generator_node", "supervisor", "__end__"]:
    """
    Determines the next step after the hallucination check node runs.
    """
    hallucination_result = state.get("hallucination_result", {})
    validation_decision = hallucination_result.get("validation_decision", "")
    layer2_attempts = state.get("layer2_attempts", 0)
    use_fallback = state.get("use_fallback_result", False)

    if validation_decision == "PASS":
        return "supervisor"
    elif validation_decision == "REGENERATE" and layer2_attempts < 2:
        return "graph_generator_node"
    elif use_fallback:
        print("[INFO] [Routing] Fallback result is in use. Terminating.")
        return "__end__"
    else:
        return "supervisor"

# =============================================================================
# Graph Assembly
# =============================================================================


print("[INFO] Building the agentic graph...")

builder = StateGraph(State)

# Add nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("ontology_research_step_node", ontology_research_step_node)
builder.add_node("ontology_synthesis_node", ontology_synthesis_node)
builder.add_node("custom_facet_node", custom_facet_node)
builder.add_node("graph_generator_node", graph_generator_node)
builder.add_node("validator_node", validator_node)
builder.add_node("hallucination_check_node", hallucination_check_node)
builder.add_node("uuid_planner_node", uuid_planner_node)
builder.add_node("invalidate_uuid_plan_node", invalidate_uuid_plan_node)

# Add edges
builder.set_entry_point("supervisor")
builder.add_edge("ontology_research_step_node", "supervisor")
builder.add_edge("ontology_synthesis_node", "supervisor")
builder.add_edge("custom_facet_node", "supervisor")
builder.add_edge("graph_generator_node", "validator_node")
builder.add_edge("uuid_planner_node", "graph_generator_node")
builder.add_edge("invalidate_uuid_plan_node", "uuid_planner_node")

# Add conditional edges
builder.add_conditional_edges("supervisor", route_supervisor)
builder.add_conditional_edges(
    "validator_node",
    route_after_validation,
    {
        "hallucination_check_node": "hallucination_check_node",
        "graph_generator_node": "graph_generator_node",
        "invalidate_uuid_plan_node": "invalidate_uuid_plan_node",
        "__end__": END,
    },
)
builder.add_conditional_edges(
    "hallucination_check_node", route_after_hallucination_check)

# Compile the graph
graph = builder.compile()

print("[SUCCESS] Graph built and compiled.")
print(f"[INFO] Graph nodes: {list(graph.nodes.keys())}")

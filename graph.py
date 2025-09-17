from langgraph.graph import StateGraph, END, START
from typing import Literal

# --- Custom Module Imports ---
from state import State
from schemas import Router
from config import llm, SUPERVISOR_AGENT_PROMPT

# Import all agent nodes
from config import llm, SUPERVISOR_AGENT_PROMPT, MAX_GRAPH_GENERATOR_ATTEMPTS
from agents.supervisor import supervisor_node
from agents.ontology_researcher import ontology_research_node
from agents.custom_facet import custom_facet_node
from agents.graph_generator import graph_generator_node
from agents.validator import validator_node
from agents.hallucination_checker import hallucination_check_node
# =============================================================================
# Routing Functions
# =============================================================================


def route_supervisor(state: State) -> str:
    """Routes from the supervisor to the appropriate worker node or ends."""

    # --- GUARDRAIL IMPLEMENTATION ---
    # First, check for a terminal failure state before asking the LLM.
    graph_attempts = state.get("graphGeneratorAttempts", 0)
    if graph_attempts >= MAX_GRAPH_GENERATOR_ATTEMPTS:
        print("[GUARDRAIL] Max graph generator attempts reached. Moving to validator.")
        return "validator_node"  # Continue workflow, don't terminate

    # If no terminal condition is met, proceed with LLM-based routing.
    messages = [
        {"role": "system", "content": SUPERVISOR_AGENT_PROMPT}] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)

    decision = response.get("next")
    if decision == "FINISH":
        print("[INFO] [Supervisor] Task complete. Terminating.")
        return "__end__"

    return decision


def route_after_validation(state: State) -> Literal["hallucination_check_node", "supervisor", "__end__"]:
    """
    Determines the next step after the structural validation node runs.
    """
    validation_result = state.get("validation_result", {})
    is_clean = validation_result.get("is_clean", False)
    validation_attempts = state.get("validationAttempts", 0)

    if is_clean:
        return "hallucination_check_node"
    elif validation_attempts >= 3:
        print("[INFO] [Routing] Max validation attempts reached. Terminating.")
        return "__end__"
    else:
        return "supervisor"


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
builder.add_node("ontology_research_node", ontology_research_node)
builder.add_node("custom_facet_node", custom_facet_node)
builder.add_node("graph_generator_node", graph_generator_node)
builder.add_node("validator_node", validator_node)
builder.add_node("hallucination_check_node", hallucination_check_node)

# Add edges
builder.set_entry_point("supervisor")
builder.add_edge("ontology_research_node", "supervisor")
builder.add_edge("custom_facet_node", "supervisor")
builder.add_edge("graph_generator_node", "validator_node")

# Add conditional edges
builder.add_conditional_edges("supervisor", route_supervisor)
builder.add_conditional_edges("validator_node", route_after_validation)
builder.add_conditional_edges(
    "hallucination_check_node", route_after_hallucination_check)

# Compile the graph
graph = builder.compile()

print("[SUCCESS] Graph built and compiled.")
print(f"[INFO] Graph nodes: {list(graph.nodes.keys())}")

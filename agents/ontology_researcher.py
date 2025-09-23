from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

# --- Custom Module Imports ---
# These are assumed to be in your project structure.
from state import State
from tools import (
    analyze_case_uco_class,
    list_case_uco_classes,
    analyze_case_uco_facets,
    analyze_case_uco_relationships,
    generate_uuid,
)
from config import llm, ONTOLOGY_RESEARCH_AGENT_PROMPT
from utils import parse_ontology_response

# =============================================================================
# Agent Setup
# =============================================================================

# Define the set of tools available to this agent for ontology research.
ontology_tools = [
    list_case_uco_classes,
    analyze_case_uco_class,
    analyze_case_uco_facets,
    analyze_case_uco_relationships,
]

# Create the specific ReAct agent. The `create_react_agent` function compiles
# the agent into a runnable that handles the entire thought-action-observation loop.
ontology_research_agent = create_react_agent(
    llm, tools=ontology_tools, state_modifier=ONTOLOGY_RESEARCH_AGENT_PROMPT)

# Define other LLM configurations if they are specific to this agent module.
# These seem to be used for tasks outside the primary ReAct agent loop.
custom_facet_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
graph_generator_llm = llm.bind_tools([generate_uuid])

# =============================================================================
# Agent Node Function
# =============================================================================


def ontology_research_node(state: State) -> dict:
    """
    This node runs the self-contained ontology research agent.

    It takes the initial user input, invokes the agent, waits for it to
    complete its entire multi-step process, and then returns the final
    Markdown and JSON report.
    """
    # Check if the research has already been done to avoid re-running.
    if state.get("ontologyMap"):
        print("[INFO] [Ontology] Research already complete, skipping.")
        return {}

    # Extract the initial user query from the message history in the state.
    input_text = ""
    messages = state.get("messages", [])
    if messages:
        # Find the first human message in the list, which contains the actual user input.
        human_message = next((m for m in messages if hasattr(m, 'type') and m.type == "human"), None)
        if human_message:
            input_text = str(human_message.content)

    # Handle cases where no input text is found.
    if not input_text:
        error_message = "[ERROR] [Ontology] Could not find initial input in state."
        print(error_message)
        return {"messages": [HumanMessage(
                content=error_message, name="ontology_research_agent")]}

    print(
        f"[INFO] [Ontology] Mapping standard ontology for: {input_text[:60]}...")

    # --- Agent Invocation ---
    # The .invoke() method runs the entire agent process from start to finish.
    # It hides all intermediate steps (like the initial tool calls) and only
    # returns the final result once the agent has finished its work.
    # To see each step, you would use .stream() and loop through the results.
    result = ontology_research_agent.invoke(
        {"messages": [("user", input_text)]})

    # The final output from the agent is the last message in the sequence.
    agent_output = result["messages"][-1].content

    # Parse the agent's final Markdown output into a structured dictionary.
    ontology_map = parse_ontology_response(agent_output)

    print("[SUCCESS] [Ontology] Research complete, updating state.")

    # Update the state with the final results and return control to the supervisor.
    return {
            "ontologyMarkdown": agent_output,
            "ontologyMap": ontology_map,
            "messages": [HumanMessage(content="Ontology research complete, summary and markdown report generated.", name="ontology_research_agent")],
        }

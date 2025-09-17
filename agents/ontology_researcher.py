from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

# --- Custom Module Imports ---
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

# Define the set of tools available to this agent
ontology_tools = [
    analyze_case_uco_class,
    list_case_uco_classes,
    analyze_case_uco_facets,
    analyze_case_uco_relationships,
]

# Create the specific ReAct agent for ontology research
ontology_research_agent = create_react_agent(
    llm, tools=ontology_tools, state_modifier=ONTOLOGY_RESEARCH_AGENT_PROMPT)

# Define other LLM configurations if they are specific to this agent module
custom_facet_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
graph_generator_llm = llm.bind_tools([generate_uuid])

# =============================================================================
# Agent Node Function
# =============================================================================


def ontology_research_node(state: State) -> Command:
    """
    The node for running the ontology research agent.
    """
    if state.get("ontologyMap"):
        print("[INFO] [Ontology] Research already complete, skipping.")
        return Command(goto="supervisor")

    # Extract the initial user query from the message history
    input_text = ""
    messages = state.get("messages", [])
    if messages:
        # The initial human input is typically the first message
        input_text = str(messages[0].content)

    if not input_text:
        error_message = "[ERROR] [Ontology] Could not find initial input in state."
        print(error_message)
        return Command(
            update={"messages": [HumanMessage(
                content=error_message, name="ontology_research_agent")]},
            goto="supervisor"
        )

    print(
        f"[INFO] [Ontology] Mapping standard ontology for: {input_text[:60]}...")

    # Invoke the ReAct agent
    result = ontology_research_agent.invoke(
        {"messages": [("user", input_text)]})
    agent_output = result["messages"][-1].content

    # Parse the agent's output into a structured dictionary
    ontology_map = parse_ontology_response(agent_output, input_text)

    print("[SUCCESS] [Ontology] Research complete, updating state.")

    return Command(
        update={
            "ontologyMarkdown": agent_output,
            "ontologyMap": ontology_map,
            "messages": [HumanMessage(content=agent_output, name="ontology_research_agent")],
        },
        goto="supervisor",
    )

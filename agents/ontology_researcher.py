from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

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

# Instead of ReAct agent, use direct LLM with tool calling
# Bind tools directly to the LLM for more reliable tool calling
ontology_research_llm = llm.bind_tools(ontology_tools)

# Define other LLM configurations if they are specific to this agent module.
# These seem to be used for tasks outside the primary ReAct agent loop.
custom_facet_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
graph_generator_llm = llm.bind_tools([generate_uuid])

# =============================================================================
# Agent Node Function
# =============================================================================


def ontology_research_step_node(state: State) -> dict:
    """
    This node runs ontology research using direct LLM tool calling.

    It takes the initial user input, uses the LLM with bound tools to research
    the ontology, and generates a markdown report.
    """
    # Check if the research has already been done to avoid re-running.
    if state.get("ontologyMarkdown"):
        print("[INFO] [Ontology Researcher] Research already complete, skipping.")
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
        error_message = "[ERROR] [Ontology Researcher] Could not find initial input in state."
        print(error_message)
        return {"messages": [HumanMessage(
                content=error_message, name="ontology_research_agent")]}

    print(f"[INFO] [Ontology Researcher] Mapping standard ontology for: {input_text[:60]}...")

    # --- Direct LLM with Tool Calling ---
    # Create messages with system prompt and user input
    all_messages = [
        SystemMessage(content=ONTOLOGY_RESEARCH_AGENT_PROMPT),
        HumanMessage(content=input_text),
    ]

    max_iterations = 12
    tool_calls_made = False
    final_response = None

    for _ in range(max_iterations):
        response = ontology_research_llm.invoke(all_messages)
        all_messages.append(response)

        tool_calls = getattr(response, "tool_calls", None) or []

        if tool_calls:
            tool_calls_made = True
            print(f"[INFO] [Ontology Researcher] Processing {len(tool_calls)} tool calls...")

            from langchain_core.messages import ToolMessage

            for tool_call in tool_calls:
                tool_name = getattr(tool_call, "name", None) or tool_call.get("name")
                tool_args = getattr(tool_call, "args", None) or tool_call.get("args") or {}
                tool_id = getattr(tool_call, "id", None) or tool_call.get("id")

                print(f"[INFO] [Tool Call] {tool_name}({tool_args})")

                tool_result = None
                for tool in ontology_tools:
                    if tool.name == tool_name:
                        try:
                            tool_result = tool.invoke(tool_args)
                            print(
                                f"[SUCCESS] [Tool Result] {tool_name} returned {len(str(tool_result))} characters"
                            )
                        except Exception as exc:
                            tool_result = f"Error executing {tool_name}: {exc}"
                            print(f"[ERROR] [Tool Error] {tool_result}")
                        break

                if tool_result is None:
                    tool_result = f"Tool {tool_name} not found"
                    print(f"[ERROR] [Tool Missing] {tool_result}")

                all_messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_id)
                )

            # Continue loop to let the LLM consume tool outputs
            continue

        if not tool_calls_made:
            print("[WARN] [Ontology Researcher] LLM responded without tool calls; requesting compliance.")
            all_messages.append(
                HumanMessage(
                    content=(
                        "You have not called any tools yet. Respond ONLY with 4-6 "
                        "list_case_uco_classes tool calls before providing any report."
                    )
                )
            )
            continue

        final_response = response
        break
    else:
        raise RuntimeError(
            "Ontology researcher exceeded maximum iterations without completing analysis."
        )

    if not tool_calls_made:
        raise RuntimeError(
            "Ontology researcher failed to execute required CASE/UCO tool calls."
        )

    # If the last assistant message after tool calls isn't final, ask for the report explicitly.
    if final_response is None or not getattr(final_response, "content", "").strip():
        print("[INFO] [Ontology Researcher] Requesting final markdown report after tool calls.")
        all_messages.append(
            HumanMessage(
                content=(
                    "Based on the tool results above, generate the complete markdown report "
                    "following the exact formatting requirements (sections, tables, final JSON block)."
                )
            )
        )
        final_response = ontology_research_llm.invoke(all_messages)

    agent_output = final_response.content if hasattr(final_response, "content") else str(final_response)

    print("[SUCCESS] [Ontology Researcher] Research complete, returning markdown report.")

    # Update the state with the final markdown report.
    return {
            "ontologyMarkdown": agent_output,
            "messages": [HumanMessage(content="Ontology research complete, markdown report generated.", name="ontology_research_agent")],
        }

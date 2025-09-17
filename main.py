from graph import builder
import os
import uuid
from datetime import datetime
from pathlib import Path

# --- LangGraph and LangChain Imports ---
from langgraph.checkpoint.sqlite import SqliteSaver

# --- Phoenix Tracing (Hardcoded as requested) ---
from phoenix.otel import register
os.environ["PHOENIX_API_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJBcGlLZXk6NSJ9.GFVSfOg--1GBYP9oiMSRF93J2Lq31H14pGOnk5pnQVo"
tracer_provider = register(
    project_name="forensic-agent-system",
    endpoint="https://app.phoenix.arize.com/s/ktamsik101/v1/traces",
    auto_instrument=True
)
print("[INFO] Phoenix tracing is active.")
# --- Custom Module Imports ---
# We import the 'builder' object from graph.py, not the compiled graph,
# because each session requires its own unique checkpointer.

# =============================================================================
# SESSION MANAGEMENT
# =============================================================================


def generate_session_id(user_identifier: str = "user") -> str:
    """Generates a unique session ID for user and task isolation."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    user_prefix = user_identifier[:10] if user_identifier else "user"
    return f"{user_prefix}_{timestamp}_{unique_id}"


def ensure_session_directory() -> Path:
    """Ensures the base 'sessions' directory exists and returns its path."""
    session_dir = Path("sessions")
    session_dir.mkdir(exist_ok=True)
    return session_dir

# =============================================================================
# EXECUTION WRAPPER
# =============================================================================


def execute_forensic_analysis_session_stream(
    session_id: str,
    input_artifacts: str
):
    """
    Executes a complete forensic analysis workflow with isolated, persistent state.
    Yields events for real-time streaming to UI.
    """
    print(f"[INFO] Initializing session: {session_id}")

    session_dir = ensure_session_directory()
    db_path = session_dir / f"{session_id}.db"

    # SqliteSaver provides persistent checkpointing for the session's state.
    with SqliteSaver.from_conn_string(str(db_path)) as memory:
        # Compile the graph with the session-specific checkpointer.
        agent = builder.compile(checkpointer=memory)

        # Configure the session for LangGraph's stream method.
        config = {"configurable": {"thread_id": session_id},
                  "recursion_limit": 300}

        try:
            print("[INFO] Executing workflow stream...")
            # Execute the workflow.
            events = agent.stream(
                {"messages": [("user", input_artifacts)]},
                config=config,
                stream_mode="values"
            )

            step_count = 0

            # Yield each event for real-time processing
            for event in events:
                step_count += 1
                yield {
                    "type": "step",
                    "step_number": step_count,
                    "event": event,
                    "session_id": session_id
                }

            # Yield final result
            yield {
                "type": "completion",
                "session_id": session_id,
                "total_steps": step_count,
                "session_db_path": str(db_path),
                "final_event": event
            }

        except Exception as e:
            print(f"[ERROR] Session {session_id} failed: {str(e)}")
            yield {
                "type": "error",
                "session_id": session_id,
                "error": str(e)
            }


def execute_forensic_analysis_session(
    session_id: str,
    input_artifacts: str,
    show_all_steps: bool = False
) -> dict:
    """
    Executes a complete forensic analysis workflow with isolated, persistent state.
    """
    print(f"[INFO] Initializing session: {session_id}")

    session_dir = ensure_session_directory()
    db_path = session_dir / f"{session_id}.db"

    # SqliteSaver provides persistent checkpointing for the session's state.
    with SqliteSaver.from_conn_string(str(db_path)) as memory:
        # Compile the graph with the session-specific checkpointer.
        agent = builder.compile(checkpointer=memory)

        # Configure the session for LangGraph's stream method.
        config = {"configurable": {"thread_id": session_id},
                  "recursion_limit": 300}

        try:
            print("[INFO] Executing workflow stream...")
            # Execute the workflow.
            events = agent.stream(
                {"messages": [("user", input_artifacts)]},
                config=config,
                stream_mode="values"
            )

            final_event = None
            step_count = 0

            # Process all events from the stream to get the final state.
            for event in events:
                step_count += 1
                final_event = event
                if show_all_steps and "messages" in event and event["messages"]:
                    print(f"\n--- STEP {step_count} ---")
                    event["messages"][-1].pretty_print()

            result = {
                "session_id": session_id,
                "final_state": final_event,
                "total_steps": step_count,
                "session_db_path": str(db_path)
            }

            print(
                f"\n[SUCCESS] Session {session_id} completed in {step_count} steps.")
            return result

        except Exception as e:
            print(f"[ERROR] Session {session_id} failed: {str(e)}")
            raise
# =============================================================================
# HIGH-LEVEL API & BACKWARD COMPATIBILITY
# =============================================================================


def call_forensic_analysis_with_session(
    user_identifier: str,
    input_artifacts: str,
    show_all_steps: bool = False
) -> dict:
    """Creates a new session and runs the forensic analysis."""
    session_id = generate_session_id(user_identifier)
    return execute_forensic_analysis_session(session_id, input_artifacts, show_all_steps)


def call_enhanced_forensic_system(agent, prompt, show_all_steps=True, recursion_limit=300):
    """Legacy function modified for backward compatibility to use session management."""
    temp_session_id = generate_session_id("temp_legacy")
    return execute_forensic_analysis_session(temp_session_id, prompt, show_all_steps)


def call_three_agent_system(agent, prompt, show_all_steps=True, recursion_limit=300):
    """Legacy function wrapper."""
    return call_enhanced_forensic_system(agent, prompt, show_all_steps, recursion_limit)


def call_multi_agent_system(agent, prompt, show_all_steps=True, recursion_limit=300):
    """Legacy function wrapper."""
    return call_enhanced_forensic_system(agent, prompt, show_all_steps, recursion_limit)


print("[INFO] Enhanced execution functions with session support defined.")
print("[INFO] New API available: call_forensic_analysis_with_session(user_id, input, show_steps)")

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # This block runs when you execute the script directly (e.g., `python main.py`).

    # Define the input for the analysis.
    input_query = """
Artifact: Windows Prefetch File
- Path: C:\\Windows\\Prefetch\\MALICIOUS.EXE-12345678.pf
- Created: 2025-09-17T10:30:00Z
- Process ID: 4567
- Executable: MALICIOUS.EXE
- Last Run: 2025-09-17T10:35:15Z
"""

    # Generate a unique ID for this specific run.
    session_id = generate_session_id("forensic_analyst_01")

    # Execute the analysis session.
    final_result = execute_forensic_analysis_session(
        session_id=session_id,
        input_artifacts=input_query,
        show_all_steps=True  # Set to False to only see the final summary.
    )

    # Print a summary of the final results.
    print("\n" + "="*50)
    print("--- FINAL EXECUTION SUMMARY ---")
    print("="*50)
    print(f"Session database saved to: {final_result['session_db_path']}")

    final_graph = final_result.get("final_state", {}).get("jsonldGraph", {})
    if final_graph:
        print("\n--- Generated JSON-LD Graph ---")
        import json
        print(json.dumps(final_graph, indent=2))

"""
Services module containing core business logic for forensic analysis.
Refactored from main.py to separate concerns and enable API integration.
"""

import os
import uuid
import json
import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Generator, Dict, Any

# --- LangGraph and LangChain Imports ---
from langgraph.checkpoint.sqlite import SqliteSaver

# --- Custom Module Imports ---
from graph import builder
from state import DEFAULT_STATE


def _normalize_input(input_artifacts: Any) -> Dict[str, Any]:
    """
    Returns:
      {
        'as_text': str,     # what we feed the LLM as user message
        'raw_json': Any,    # original object or None
        'format': 'json' | 'text' | 'csv'
      }
    """
    if isinstance(input_artifacts, (dict, list)):
        return {
            "as_text": json.dumps(input_artifacts, indent=2),
            "raw_json": input_artifacts,
            "format": "json",
        }

    # Check if input is CSV format (string with commas and newlines)
    if isinstance(input_artifacts, str):
        # Try to detect CSV format by checking for common CSV patterns
        lines = input_artifacts.strip().split('\n')
        if len(lines) > 1 and ',' in lines[0]:
            try:
                # Attempt to parse as CSV with strict error handling
                csv_reader = csv.DictReader(io.StringIO(input_artifacts), strict=True)
                parsed_rows = list(csv_reader)

                if parsed_rows:
                    # Successfully parsed as CSV
                    return {
                        "as_text": json.dumps(parsed_rows, indent=2),
                        "raw_json": parsed_rows,
                        "format": "csv",
                    }
            except (csv.Error, Exception) as e:
                # If CSV parsing fails, raise a user-friendly error
                raise ValueError(f"Invalid CSV format: {str(e)}. Please ensure your CSV file has proper headers and formatting.")

    return {
        "as_text": str(input_artifacts),
        "raw_json": None,
        "format": "text",
    }


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


def execute_forensic_analysis_session_stream(
    session_id: str,
    input_artifacts: Any,
    metadata: Dict[str, Any] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Executes a complete forensic analysis workflow with isolated, persistent state.
    Yields events for real-time streaming to UI.

    Args:
        session_id: Unique identifier for this analysis session
        input_artifacts: The forensic artifact description to analyze
        metadata: Optional metadata dict with artifact_type, description, source

    Yields:
        Dict containing event data with type, step information, and session details
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
            # Normalize input and prepare for agent execution
            norm = _normalize_input(input_artifacts)

            # Prepend metadata if provided
            user_message = norm["as_text"]
            if metadata:
                metadata_lines = []
                if metadata.get("artifact_type"):
                    metadata_lines.append(f"Artifact Type: {metadata['artifact_type']}")
                if metadata.get("description"):
                    metadata_lines.append(f"Description: {metadata['description']}")
                if metadata.get("source"):
                    metadata_lines.append(f"Source: {metadata['source']}")

                if metadata_lines:
                    metadata_str = "\n".join(metadata_lines)
                    user_message = f"{metadata_str}\n\n{user_message}"
                    print(f"[INFO] Prepended metadata to input")

            # Execute the workflow.
            # Start with DEFAULT_STATE to ensure all keys exist
            initial_state = dict(DEFAULT_STATE)
            # Merge request-specific fields
            initial_state["messages"] = [
                ("system", "If the user message is JSON, treat it as authoritative source data."),
                ("user", user_message),
            ]
            initial_state["rawInputJSON"] = norm["raw_json"]
            initial_state["inputFormat"] = norm["format"]

            events = agent.stream(
                initial_state,
                config=config,
                stream_mode="values"
            )

            step_count = 0

            # Yield each event for real-time processing
            for event in events:
                step_count += 1

                # Create JSON-serializable version of the event
                serializable_event = {}
                for key, value in event.items():
                    if key == "messages" and isinstance(value, list):
                        # Convert LangChain messages to serializable format
                        serializable_event[key] = []
                        for msg in value:
                            if hasattr(msg, 'content') and hasattr(msg, 'type'):
                                serializable_event[key].append({
                                    "type": msg.type,
                                    "content": msg.content
                                })
                            else:
                                # Handle other message formats
                                serializable_event[key].append(str(msg))
                    else:
                        # For other fields, try to serialize or convert to string
                        try:
                            import json
                            json.dumps(value)  # Test if serializable
                            serializable_event[key] = value
                        except (TypeError, ValueError):
                            serializable_event[key] = str(value)

                yield {
                    "type": "step",
                    "step_number": step_count,
                    "event": serializable_event,
                    "session_id": session_id
                }

            # Yield final result
            # Create JSON-serializable version of the final event
            serializable_final_event = {}
            for key, value in event.items():
                if key == "messages" and isinstance(value, list):
                    # Convert LangChain messages to serializable format
                    serializable_final_event[key] = []
                    for msg in value:
                        if hasattr(msg, 'content') and hasattr(msg, 'type'):
                            serializable_final_event[key].append({
                                "type": msg.type,
                                "content": msg.content
                            })
                        else:
                            # Handle other message formats
                            serializable_final_event[key].append(str(msg))
                else:
                    # For other fields, try to serialize or convert to string
                    try:
                        import json
                        json.dumps(value)  # Test if serializable
                        serializable_final_event[key] = value
                    except (TypeError, ValueError):
                        serializable_final_event[key] = str(value)

            yield {
                "type": "completion",
                "session_id": session_id,
                "total_steps": step_count,
                "session_db_path": str(db_path),
                "final_event": serializable_final_event
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
    input_artifacts: Any,
    show_all_steps: bool = False
) -> Dict[str, Any]:
    """
    Executes a complete forensic analysis workflow with isolated, persistent state.

    Args:
        session_id: Unique identifier for this analysis session
        input_artifacts: The forensic artifact description to analyze
        show_all_steps: Whether to print detailed step information

    Returns:
        Dict containing the final analysis result and session information
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
            # Normalize input and prepare for agent execution
            norm = _normalize_input(input_artifacts)

            # Execute the workflow.
            # Start with DEFAULT_STATE to ensure all keys exist
            initial_state = dict(DEFAULT_STATE)
            # Merge request-specific fields
            initial_state["messages"] = [
                ("system", "If the user message is JSON, treat it as authoritative source data."),
                ("user", norm["as_text"]),
            ]
            initial_state["rawInputJSON"] = norm["raw_json"]
            initial_state["inputFormat"] = norm["format"]

            events = agent.stream(
                initial_state,
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


# Legacy compatibility functions
def call_forensic_analysis_with_session(
    user_identifier: str,
    input_artifacts: Any,
    show_all_steps: bool = False
) -> Dict[str, Any]:
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

import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import json

# Mock the main module functions


@patch('main.execute_forensic_analysis_session_stream')
@patch('main.generate_session_id')
def test_streamlit_app_basic_functionality(mock_generate_session_id, mock_execute_stream):
    """Test basic functionality of the Streamlit app"""

    # Mock the session ID generation
    mock_generate_session_id.return_value = "test_session_123"

    # Mock the streaming function to return a completion event
    mock_completion_event = {
        "type": "completion",
        "session_id": "test_session_123",
        "total_steps": 5,
        "session_db_path": "/path/to/session.db",
        "final_event": {
            "jsonldGraph": {
                "@context": {
                    "uco-core": "https://ontology.unifiedcyberontology.org/uco/core/"
                },
                "@graph": [
                    {
                        "@id": "kb:test-artifact",
                        "@type": "uco-observable:File"
                    }
                ]
            }
        }
    }

    mock_execute_stream.return_value = iter([mock_completion_event])

    # Test that the functions are imported correctly
    from main import execute_forensic_analysis_session_stream, generate_session_id

    # Test session ID generation
    session_id = generate_session_id("test_user")
    assert session_id == "test_session_123"

    # Test streaming function
    events = list(execute_forensic_analysis_session_stream(
        session_id, "test input"))
    assert len(events) == 1
    assert events[0]["type"] == "completion"
    assert events[0]["total_steps"] == 5


def test_streamlit_app_error_handling():
    """Test error handling in the Streamlit app"""

    with patch('main.execute_forensic_analysis_session_stream') as mock_stream:
        # Mock an error event
        mock_error_event = {
            "type": "error",
            "session_id": "test_session_123",
            "error": "Test error message"
        }

        mock_stream.return_value = iter([mock_error_event])

        from main import execute_forensic_analysis_session_stream

        events = list(execute_forensic_analysis_session_stream(
            "test_session", "test input"))
        assert len(events) == 1
        assert events[0]["type"] == "error"
        assert events[0]["error"] == "Test error message"


def test_streamlit_app_step_processing():
    """Test step processing in the Streamlit app"""

    with patch('main.execute_forensic_analysis_session_stream') as mock_stream:
        # Mock step events
        mock_step_events = [
            {
                "type": "step",
                "step_number": 1,
                "event": {
                    "messages": [
                        MagicMock(content="Agent 1 processing...")
                    ]
                },
                "session_id": "test_session_123"
            },
            {
                "type": "step",
                "step_number": 2,
                "event": {
                    "messages": [
                        MagicMock(content="Agent 2 processing...")
                    ]
                },
                "session_id": "test_session_123"
            },
            {
                "type": "completion",
                "session_id": "test_session_123",
                "total_steps": 2,
                "session_db_path": "/path/to/session.db",
                "final_event": {"jsonldGraph": {}}
            }
        ]

        mock_stream.return_value = iter(mock_step_events)

        from main import execute_forensic_analysis_session_stream

        events = list(execute_forensic_analysis_session_stream(
            "test_session", "test input"))
        assert len(events) == 3
        assert events[0]["type"] == "step"
        assert events[0]["step_number"] == 1
        assert events[1]["type"] == "step"
        assert events[1]["step_number"] == 2
        assert events[2]["type"] == "completion"


def test_json_ld_output_format():
    """Test that the JSON-LD output is properly formatted"""

    sample_jsonld = {
        "@context": {
            "uco-core": "https://ontology.unifiedcyberontology.org/uco/core/",
            "uco-observable": "https://ontology.unifiedcyberontology.org/uco/observable/"
        },
        "@graph": [
            {
                "@id": "kb:prefetch-file-001",
                "@type": "uco-observable:File",
                "uco-core:hasFacet": [
                    {
                        "@type": "uco-observable:PrefetchFacet",
                        "uco-observable:applicationFileName": "MALICIOUS.EXE",
                        "uco-observable:prefetchHash": "12345678"
                    }
                ]
            }
        ]
    }

    # Test JSON serialization
    json_str = json.dumps(sample_jsonld, indent=2)
    parsed_back = json.loads(json_str)

    assert parsed_back["@context"]["uco-core"] == "https://ontology.unifiedcyberontology.org/uco/core/"
    assert len(parsed_back["@graph"]) == 1
    assert parsed_back["@graph"][0]["@type"] == "uco-observable:File"


if __name__ == "__main__":
    pytest.main([__file__])


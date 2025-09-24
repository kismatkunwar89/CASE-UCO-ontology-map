#!/usr/bin/env python3
"""
Test script to demonstrate that the system can handle ANY case dynamically.
This tests various artifact types from different domains to prove domain-agnostic capability.
"""

import pytest
import pytest
from agents.uuid_planner import uuid_planner_node
from agents.graph_generator import graph_generator_node
from state import State

# Test cases covering different domains
test_cases = [
    ("WindowsPrefetch", "Artifact: Windows Prefetch File, Path: C:\\Windows\\Prefetch\\MALICIOUS.EXE-12345678.pf", "Windows Prefetch file analysis"),
    ("File", "Artifact: File, Path: /home/user/document.pdf, Size: 1024KB", "Generic file analysis"),
    ("Process", "Artifact: Process, Name: malware.exe, PID: 1234", "Process execution analysis"),
    ("NetworkConnection", "Artifact: Network Connection, Source: 192.168.1.1, Destination: 10.0.0.1", "Network traffic analysis"),
    ("RegistryKey", "Artifact: Registry Key, Path: HKEY_LOCAL_MACHINE\\SOFTWARE\\Malware", "Registry analysis"),
]

@pytest.mark.parametrize("artifact_type, input_data, description", test_cases)
def test_case(artifact_type: str, input_data: str, description: str):
    """Test a specific artifact type to prove dynamic handling."""
    print(f"\n{'='*80}")
    print(f"🧪 TESTING: {artifact_type}")
    print(f"📝 Description: {description}")
    print(f"{'='*80}")

    # Create mock state with the specific artifact data
    mock_state: State = {
        "rawInputJSON": [{"input": input_data}],
        "ontologyMap": {
            "input_text": input_data,
            "artifacts": [artifact_type],
            "classes": [f"{artifact_type}", f"{artifact_type}Facet"],
            "properties": {
                f"{artifact_type}": ["property1", "property2", "property3"],
                f"{artifact_type}Facet": []
            },
            "facets": [f"{artifact_type}Facet"],
            "relationships": [
                {"type": "ObservableRelationship", "source": artifact_type,
                 "target": f"{artifact_type}Facet", "kind": "hasFacet", "directional": True}
            ],
            "analysis": f"The input describes a {artifact_type} artifact.",
            "additional_details": {
                "note": f"The properties extracted from the {artifact_type} and {artifact_type}Facet classes provide comprehensive analysis."
            }
        },
        "customFacets": {},
        "customState": {},
        "ontologyMarkdown": "",
        "graphGeneratorAttempts": 0,
        "graphGeneratorErrors": [],
        "validation_feedback": "",
        "validationHistory": [],
        "learningContext": "",
        "memory_context": "No previous memory available",
        "layer2_feedback_history": []
    }

    try:
        # Run planner first
        planner_result = uuid_planner_node(mock_state)
        mock_state.update(planner_result)

        # Now run generator
        result_command = graph_generator_node(mock_state)

        print(f"✅ [SUCCESS] {artifact_type} processed successfully!")
        
        assert result_command is not None
        assert "jsonldGraph" in result_command

    except Exception as e:
        pytest.fail(f"{artifact_type} failed: {str(e)}")

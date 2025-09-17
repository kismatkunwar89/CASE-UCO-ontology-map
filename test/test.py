import json
from agents.graph_generator import graph_generator_node
from state import State

# =============================================================================
# COMPREHENSIVE TEST FOR THE GRAPH GENERATOR NODE
# =============================================================================

print("[INFO] Setting up comprehensive test for the Graph Generator node...")
print("="*80)

# 1. Create a realistic mock State object based on the terminal output
# This simulates the data after ontology_research_node and custom_facet_node have run
mock_state: State = {
    "messages": [
        # Simulate the original user message
        type("Message", (), {
            "content": """Artifact: Windows Prefetch File
- Path: C:\\Windows\\Prefetch\\MALICIOUS.EXE-12345678.pf
- Created: 2025-09-17T10:30:00Z
- Process ID: 4567
- Executable: MALICIOUS.EXE
- Last Run: 2025-09-17T10:35:15Z"""
        })(),
        # Simulate ontology research agent output
        type("Message", (), {
            "content": "Ontology research completed - identified WindowsPrefetch class",
            "name": "ontology_research_agent"
        })(),
        # Simulate custom facet agent output
        type("Message", (), {
            "content": "Custom facets analysis completed",
            "name": "custom_facet_agent"
        })()
    ],

    # Realistic ontology mapping based on terminal output
    "ontologyMap": {
        "input_text": "Artifact: Windows Prefetch File...",
        "artifacts": ["Windows Prefetch File"],
        "classes": ["WindowsPrefetch", "WindowsPrefetchFacet"],
        "properties": {
            "WindowsPrefetch": ["accessedDirectory", "accessedFile", "applicationFileName", "firstRun", "lastRun", "prefetchHash", "timesExecuted", "volume"],
            "WindowsPrefetchFacet": []
        },
        "facets": ["WindowsPrefetchFacet"],
        "relationships": [
            {"type": "ObservableRelationship", "source": "WindowsPrefetch",
                "target": "WindowsPrefetchFacet", "kind": "hasFacet", "directional": True}
        ],
        "analysis": "The input describes a Windows Prefetch file, which is mapped to the WindowsPrefetch class.",
        "additional_details": {
            "note": "The properties extracted from the WindowsPrefetch and WindowsPrefetchFacet classes provide a comprehensive view of the prefetch file's characteristics."
        }
    },

    # Detailed ontology markdown from the terminal output
    "ontologyMarkdown": """# Ontology Research Report

**Input Text**
> Artifact: Windows Prefetch File  
> - Path: C:\\Windows\\Prefetch\\MALICIOUS.EXE-12345678.pf  
> - Created: 2025-09-17T10:30:00Z  
> - Process ID: 4567  
> - Executable: MALICIOUS.EXE  
> - Last Run: 2025-09-17T10:35:15Z  

## Summary
- **Identified Artifacts:** Windows Prefetch File
- **Relevant CASE/UCO Classes (Top N):** WindowsPrefetch, WindowsPrefetchFacet
- **Relevant CASE/UCO Classes Properties (Of all Top N):** accessedDirectory, accessedFile, applicationFileName, firstRun, lastRun, prefetchHash, timesExecuted, volume
- **Applicable Facets (Duck Typing):** WindowsPrefetchFacet
- **Facet Properties:** accessedDirectory, accessedFile, applicationFileName, firstRun, lastRun, prefetchHash, timesExecuted, volume
- **Relationship Patterns:** WindowsPrefetch → hasFacet → WindowsPrefetchFacet

## Detailed Class Documentation
### WindowsPrefetch
# WindowsPrefetch
**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/WindowsPrefetch`

**Description:** The Windows prefetch contains entries in a Windows prefetch file (used to speed up application startup starting with Windows XP).

## Property Shapes
By the associated SHACL property shapes, instances of WindowsPrefetch can have the following properties:

| PROPERTY | PROPERTY TYPE | DESCRIPTION | MIN COUNT | MAX COUNT | LOCAL RANGE | GLOBAL RANGE |
|----------|---------------|-------------|-----------|-----------|-------------|--------------|
| **WindowsPrefetchFacet** | | | | | | |
| accessedDirectory | ObjectProperty | Directories accessed by the prefetch application | None | None | ObservableObject | ObservableObject |
| accessedFile | ObjectProperty | Files (e.g., DLLs and other support files) used by the prefetch application | None | None | ObservableObject | ObservableObject |
| applicationFileName | DatatypeProperty | Name of the executable of the prefetch file | None | 1 | string | None |
| firstRun | DatatypeProperty | Timestamp of when the prefetch application was first executed | None | 1 | dateTime | None |
| lastRun | DatatypeProperty | Timestamp of when the prefetch application was last executed | None | 1 | dateTime | None |
| prefetchHash | DatatypeProperty | An eight character hash of the location from which the prefetch application was executed | None | 1 | string | None |
| timesExecuted | DatatypeProperty | The number of times the prefetch application has executed | None | 1 | integer | None |
| volume | ObjectProperty | The volume from which the prefetch application was executed | None | 1 | ObservableObject | ObservableObject |""",

    # Custom facets (empty in this case as per terminal output)
    "customFacets": {},
    "customState": {
        "totalCustomFacets": 0,
        "extensionNamespace": "dfc-ext",
        "reasoningApplied": True,
        "customFacetsNeeded": False,
        "dataCoverageComplete": True,
        "reasoning": "All data elements successfully mapped to standard CASE/UCO properties"
    },

    # Test scenario state
    "graphGeneratorAttempts": 0,
    "layer2_feedback_history": [],
    "graphGeneratorErrors": [],
    "validation_feedback": "",
    "validation_result": {},
    "validationHistory": [],
    "learningContext": "",
    "memory_context": ""
}

# =============================================================================
# TEST SCENARIOS
# =============================================================================


def test_scenario(scenario_name: str, state: State, description: str):
    """Run a test scenario and report results"""
    print(f"\n{'='*80}")
    print(f"🧪 TEST SCENARIO: {scenario_name}")
    print(f"📝 Description: {description}")
    print(f"{'='*80}")

    try:
        result_command = graph_generator_node(state)

        print(f"\n✅ [SUCCESS] Node execution completed")
        print(f"🎯 Command goto: {result_command.goto}")

        if result_command.update:
            print(f"📊 Updates provided: {list(result_command.update.keys())}")

            if "jsonldGraph" in result_command.update:
                graph = result_command.update["jsonldGraph"]
                print(f"📦 JSON-LD Graph generated:")
                print(
                    f"   - @context keys: {list(graph.get('@context', {}).keys())}")
                print(f"   - @graph entities: {len(graph.get('@graph', []))}")

                if graph.get('@graph'):
                    print(
                        f"   - First entity type: {graph['@graph'][0].get('@type', 'Unknown')}")

                # Show the full JSON-LD if it's not too large
                if len(json.dumps(graph, indent=2)) < 2000:
                    print(f"\n--- Full JSON-LD Graph ---")
                    print(json.dumps(graph, indent=2))
                else:
                    print(f"\n--- JSON-LD Graph Preview ---")
                    print(json.dumps(graph, indent=2)[:1000] + "...")

            if "graphGeneratorAttempts" in result_command.update:
                print(
                    f"🔄 Attempts: {result_command.update['graphGeneratorAttempts']}")

            if "graphGeneratorErrors" in result_command.update:
                errors = result_command.update['graphGeneratorErrors']
                if errors:
                    print(f"❌ Errors: {errors}")
                else:
                    print(f"✅ No errors")
        else:
            print(f"⚠️ No updates provided")

    except Exception as e:
        print(f"❌ [FATAL] Test failed: {e}")
        import traceback
        traceback.print_exc()


# Test 1: Normal successful case
print("[INFO] Starting comprehensive test scenarios...")
test_scenario(
    "Normal Success Case",
    mock_state,
    "Test the graph generator with realistic input data from ontology research"
)

# Test 2: Max attempts reached scenario
max_attempts_state = mock_state.copy()
max_attempts_state["graphGeneratorAttempts"] = 3  # At max attempts
test_scenario(
    "Max Attempts Reached",
    max_attempts_state,
    "Test fallback behavior when max attempts (3) are reached"
)

# Test 3: With validation feedback
validation_feedback_state = mock_state.copy()
validation_feedback_state["validation_feedback"] = "UUID generation failed - missing @id values"
validation_feedback_state["validation_result"] = {"is_clean": False}
test_scenario(
    "With Validation Feedback",
    validation_feedback_state,
    "Test correction behavior when validation feedback is provided"
)

# Test 4: With hallucination feedback
hallucination_feedback_state = mock_state.copy()
hallucination_feedback_state["layer2_feedback_history"] = [
    "Fabricated timestamp detected: '2025-09-17T10:30:00Z' not in original input",
    "Remove fabricated endTime property"
]
test_scenario(
    "With Hallucination Feedback",
    hallucination_feedback_state,
    "Test dynamic correction when hallucination feedback is present"
)

# Test 5: Empty ontology map
empty_ontology_state = mock_state.copy()
empty_ontology_state["ontologyMap"] = {}
test_scenario(
    "Empty Ontology Map",
    empty_ontology_state,
    "Test behavior when ontology mapping is empty"
)

print(f"\n{'='*80}")
print("🏁 ALL TEST SCENARIOS COMPLETED")
print(f"{'='*80}")

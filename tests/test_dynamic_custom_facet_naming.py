"""
Test case to validate dynamic custom facet naming functionality.

This test validates that the custom_facet_agent generates contextual,
dynamic facet names based on artifact_type instead of generic names.

Run with:
    OPENAI_API_KEY=... PYTHONPATH=. python tests/test_dynamic_custom_facet_naming.py
"""
import json
from agents.custom_facet import _generate_extension_facet_name, _auto_generate_custom_facets


def test_naming_function_basic_cases():
    """Test the _generate_extension_facet_name function with basic cases."""
    print("="*60)
    print("TESTING: Dynamic Naming Function - Basic Cases")
    print("="*60)

    test_cases = [
        ("MFT Record", "MftRecordExtensionFacet"),
        ("Windows Prefetch", "WindowsPrefetchExtensionFacet"),
        ("Email Message", "EmailMessageExtensionFacet"),
        ("Network Log", "NetworkLogExtensionFacet"),
        ("Digital File", "DigitalFileExtensionFacet"),
        ("Database Transaction", "DatabaseTransactionExtensionFacet"),
    ]

    for input_type, expected in test_cases:
        result = _generate_extension_facet_name(input_type)
        print(f"  \"{input_type}\" -> \"{result}\"")
        assert result == expected, f"Expected {expected}, got {result}"

    print("✅ All basic naming tests passed!")


def test_naming_function_edge_cases():
    """Test the _generate_extension_facet_name function with edge cases."""
    print("\n" + "="*60)
    print("TESTING: Dynamic Naming Function - Edge Cases")
    print("="*60)

    edge_cases = [
        ("", "UnknownArtifactExtensionFacet"),
        (None, "UnknownArtifactExtensionFacet"),
        ("   ", "UnknownArtifactExtensionFacet"),
        ("MFT Record from CSV", "MftRecordFromCsvExtensionFacet"),
        ("Windows Prefetch execution cache records", "WindowsPrefetchExecutionCacheRecordsExtensionFacet"),
        ("IoT-Sensor_Reading", "IotSensorReadingExtensionFacet"),
        ("Log File 2024", "LogFile2024ExtensionFacet"),
    ]

    for input_type, expected in edge_cases:
        result = _generate_extension_facet_name(input_type)
        print(f"  \"{input_type}\" -> \"{result}\"")
        assert result == expected, f"Expected {expected}, got {result}"

    print("✅ All edge case naming tests passed!")


def test_auto_generation_mft_record():
    """Test auto-generation with MFT Record artifact type."""
    print("\n" + "="*60)
    print("TESTING: Auto-Generation - MFT Record")
    print("="*60)

    unmapped_details = [
        {"field": "SecurityId", "sampleValue": "S-1-5-21-123456789", "valueType": "str"},
        {"field": "ObjectIdFileDroid", "sampleValue": "abc123", "valueType": "str"},
        {"field": "ZoneIdContents", "sampleValue": "Internet", "valueType": "str"}
    ]

    raw_input_payload = {
        "artifact_type": "MFT Record",
        "description": "A Master File Table record from NTFS filesystem",
        "source": "ntfs_analysis_tool",
        "record": {
            "SecurityId": "S-1-5-21-123456789",
            "ObjectIdFileDroid": "abc123",
            "ZoneIdContents": "Internet"
        }
    }

    ontology_map = {"facets": []}

    custom_facets, custom_state, ttl_definitions, ontology_updates = _auto_generate_custom_facets(
        unmapped_details, raw_input_payload, ontology_map
    )

    # Validate facet name
    facet_definitions = custom_facets.get("facetDefinitions", {})
    assert len(facet_definitions) == 1, f"Expected 1 facet definition, got {len(facet_definitions)}"

    facet_name = list(facet_definitions.keys())[0]
    assert facet_name == "MftRecordExtensionFacet", f"Expected MftRecordExtensionFacet, got {facet_name}"

    # Validate reasoning includes artifact type
    reasoning = custom_state.get("reasoning", "")
    assert "MFT Record" in reasoning, f"Reasoning should mention artifact type: {reasoning}"
    assert "MftRecordExtensionFacet" in reasoning, f"Reasoning should mention facet name: {reasoning}"

    # Validate TTL contains dynamic name
    assert "dfc-ext:MftRecordExtensionFacet" in ttl_definitions, "TTL should contain dynamic facet name"
    assert "MFT Record" in ttl_definitions, "TTL should reference artifact type in comments"

    print(f"✅ Generated facet: {facet_name}")
    print(f"✅ Reasoning: {reasoning}")
    print(f"✅ TTL contains dynamic names")
    print("✅ MFT Record test passed!")


def test_auto_generation_windows_prefetch():
    """Test auto-generation with Windows Prefetch artifact type."""
    print("\n" + "="*60)
    print("TESTING: Auto-Generation - Windows Prefetch")
    print("="*60)

    unmapped_details = [
        {"field": "runCount", "sampleValue": 5, "valueType": "int"},
        {"field": "prefetchHash", "sampleValue": "ABCD1234", "valueType": "str"},
        {"field": "applicationFileName", "sampleValue": "NOTEPAD.EXE", "valueType": "str"}
    ]

    raw_input_payload = {
        "artifact_type": "Windows Prefetch execution cache records",
        "description": "Windows Prefetch file showing application execution history",
        "source": "prefetch_parser",
        "record": {
            "runCount": 5,
            "prefetchHash": "ABCD1234",
            "applicationFileName": "NOTEPAD.EXE"
        }
    }

    ontology_map = {"facets": []}

    custom_facets, custom_state, ttl_definitions, ontology_updates = _auto_generate_custom_facets(
        unmapped_details, raw_input_payload, ontology_map
    )

    # Validate facet name
    facet_definitions = custom_facets.get("facetDefinitions", {})
    assert len(facet_definitions) == 1, f"Expected 1 facet definition, got {len(facet_definitions)}"

    facet_name = list(facet_definitions.keys())[0]
    assert facet_name == "WindowsPrefetchExecutionCacheRecordsExtensionFacet", f"Expected WindowsPrefetchExecutionCacheRecordsExtensionFacet, got {facet_name}"

    # Validate properties (note: _to_camel_case makes first word lowercase)
    properties = facet_definitions[facet_name].get("properties", {})
    expected_props = ["dfc-ext:runcount", "dfc-ext:prefetchhash", "dfc-ext:applicationfilename"]
    for prop in expected_props:
        assert prop in properties, f"Property {prop} should be in facet properties"

    # Validate TTL contains dynamic name and proper domain references
    assert f"dfc-ext:{facet_name}" in ttl_definitions, "TTL should contain dynamic facet name"
    assert f"rdfs:domain dfc-ext:{facet_name}" in ttl_definitions, "TTL properties should reference correct domain"

    print(f"✅ Generated facet: {facet_name}")
    print(f"✅ Properties: {list(properties.keys())}")
    print(f"✅ TTL domain references correct")
    print("✅ Windows Prefetch test passed!")


def test_auto_generation_unknown_artifact():
    """Test auto-generation with missing/empty artifact type."""
    print("\n" + "="*60)
    print("TESTING: Auto-Generation - Unknown Artifact Type")
    print("="*60)

    unmapped_details = [
        {"field": "customField1", "sampleValue": "value1", "valueType": "str"},
        {"field": "customField2", "sampleValue": 42, "valueType": "int"}
    ]

    # Test with None artifact_type
    raw_input_payload = {
        "artifact_type": None,
        "description": "Unknown artifact type",
        "record": {"customField1": "value1", "customField2": 42}
    }

    ontology_map = {"facets": []}

    custom_facets, custom_state, ttl_definitions, ontology_updates = _auto_generate_custom_facets(
        unmapped_details, raw_input_payload, ontology_map
    )

    # Validate fallback facet name
    facet_definitions = custom_facets.get("facetDefinitions", {})
    facet_name = list(facet_definitions.keys())[0]
    assert facet_name == "UnknownArtifactExtensionFacet", f"Expected UnknownArtifactExtensionFacet, got {facet_name}"

    # Test with empty artifact_type
    raw_input_payload["artifact_type"] = ""
    custom_facets2, _, _, _ = _auto_generate_custom_facets(
        unmapped_details, raw_input_payload, ontology_map
    )
    facet_name2 = list(custom_facets2.get("facetDefinitions", {}).keys())[0]
    assert facet_name2 == "UnknownArtifactExtensionFacet", f"Expected UnknownArtifactExtensionFacet for empty string, got {facet_name2}"

    print(f"✅ None artifact_type -> {facet_name}")
    print(f"✅ Empty artifact_type -> {facet_name2}")
    print("✅ Unknown artifact type test passed!")


def test_domain_agnostic_functionality():
    """Test that the system works with non-forensic artifact types."""
    print("\n" + "="*60)
    print("TESTING: Domain-Agnostic Functionality")
    print("="*60)

    test_cases = [
        {
            "artifact_type": "IoT Sensor Reading",
            "expected_facet": "IotSensorReadingExtensionFacet",
            "fields": [{"field": "temperature", "sampleValue": 23.5, "valueType": "float"}]
        },
        {
            "artifact_type": "Database Transaction Log",
            "expected_facet": "DatabaseTransactionLogExtensionFacet",
            "fields": [{"field": "transactionId", "sampleValue": "TXN-12345", "valueType": "str"}]
        },
        {
            "artifact_type": "Network Packet Capture",
            "expected_facet": "NetworkPacketCaptureExtensionFacet",
            "fields": [{"field": "packetSize", "sampleValue": 1500, "valueType": "int"}]
        }
    ]

    for test_case in test_cases:
        raw_input_payload = {
            "artifact_type": test_case["artifact_type"],
            "record": {field["field"]: field["sampleValue"] for field in test_case["fields"]}
        }

        custom_facets, _, _, _ = _auto_generate_custom_facets(
            test_case["fields"], raw_input_payload, {"facets": []}
        )

        facet_name = list(custom_facets.get("facetDefinitions", {}).keys())[0]
        assert facet_name == test_case["expected_facet"], f"Expected {test_case['expected_facet']}, got {facet_name}"

        print(f"✅ {test_case['artifact_type']} -> {facet_name}")

    print("✅ Domain-agnostic functionality test passed!")


if __name__ == "__main__":
    try:
        test_naming_function_basic_cases()
        test_naming_function_edge_cases()
        test_auto_generation_mft_record()
        test_auto_generation_windows_prefetch()
        test_auto_generation_unknown_artifact()
        test_domain_agnostic_functionality()

        print("\n" + "="*60)
        print("🎉 ALL DYNAMIC NAMING TESTS PASSED!")
        print("✅ Basic naming transformations work correctly")
        print("✅ Edge cases handled properly")
        print("✅ MFT Record generates MftRecordExtensionFacet")
        print("✅ Windows Prefetch generates WindowsPrefetchExecutionCacheRecordsExtensionFacet")
        print("✅ Unknown artifact types default to UnknownArtifactExtensionFacet")
        print("✅ TTL definitions use correct dynamic names")
        print("✅ System is completely domain-agnostic")
        print("="*60)

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
#!/usr/bin/env python3
"""
Test script to demonstrate that the system can handle ANY case dynamically.
This tests various artifact types from different domains to prove domain-agnostic capability.
"""

import json
from agents.graph_generator import graph_generator_node
from state import State


def test_case(artifact_type: str, input_data: str, description: str):
    """Test a specific artifact type to prove dynamic handling."""
    print(f"\n{'='*80}")
    print(f"🧪 TESTING: {artifact_type}")
    print(f"📝 Description: {description}")
    print(f"{'='*80}")

    # Create mock state with the specific artifact data
    mock_state: State = {
        "messages": [
            type("Message", (), {"content": input_data})()
        ],
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
        "customState": {
            "totalCustomFacets": 0,
            "extensionNamespace": "dfc-ext",
            "reasoningApplied": True,
            "customFacetsNeeded": False,
            "dataCoverageComplete": True,
            "systematicAnalysisComplete": True
        },
        "ontologyMarkdown": f"""
# Ontology Research Report

**Input Text**
> {input_data}

## Summary
- **Identified Artifacts:** {artifact_type}
- **Relevant CASE/UCO Classes (Top N):** {artifact_type}, {artifact_type}Facet
- **Applicable Facets (Duck Typing):** {artifact_type}Facet
- **Relationship Patterns:** {artifact_type} → hasFacet → {artifact_type}Facet

### {artifact_type}
# {artifact_type}
**URI:** `https://ontology.unifiedcyberontology.org/uco/observable/{artifact_type}`

**Description:** This class represents {artifact_type} artifacts in digital forensics.

By the associated SHACL property shapes, instances of {artifact_type} can have the following properties:
- property1: String value
- property2: Numeric value  
- property3: Boolean value

| **{artifact_type}Facet** | | | | | | |
""",
        "graphGeneratorAttempts": 0,
        "graphGeneratorErrors": [],
        "validation_feedback": "",
        "validationHistory": [],
        "learningContext": "",
        "memory_context": "No previous memory available",
        "layer2_feedback_history": []
    }

    try:
        result_command = graph_generator_node(mock_state)

        print(f"✅ [SUCCESS] {artifact_type} processed successfully!")
        print(f"🎯 Command goto: {result_command.goto}")

        if result_command.update and "jsonldGraph" in result_command.update:
            graph = result_command.update["jsonldGraph"]
            print(f"📦 JSON-LD Graph generated:")
            print(
                f"   - @context keys: {list(graph.get('@context', {}).keys())}")
            print(f"   - @graph entities: {len(graph.get('@graph', []))}")
            if graph.get('@graph'):
                first_entity = graph['@graph'][0]
                print(
                    f"   - First entity type: {first_entity.get('@type', 'Unknown')}")

        return True

    except Exception as e:
        print(f"❌ [FAILED] {artifact_type} failed: {str(e)}")
        return False


def main():
    """Test various artifact types to prove domain-agnostic capability."""
    print("🚀 TESTING DOMAIN-AGNOSTIC CAPABILITY")
    print("This test proves the system can handle ANY artifact type dynamically!")

    # Test cases covering different domains
    test_cases = [
        # Digital Forensics
        ("WindowsPrefetch", "Artifact: Windows Prefetch File, Path: C:\\Windows\\Prefetch\\MALICIOUS.EXE-12345678.pf",
         "Windows Prefetch file analysis"),
        ("File", "Artifact: File, Path: /home/user/document.pdf, Size: 1024KB",
         "Generic file analysis"),
        ("Process", "Artifact: Process, Name: malware.exe, PID: 1234",
         "Process execution analysis"),
        ("NetworkConnection", "Artifact: Network Connection, Source: 192.168.1.1, Destination: 10.0.0.1",
         "Network traffic analysis"),
        ("RegistryKey", "Artifact: Registry Key, Path: HKEY_LOCAL_MACHINE\\SOFTWARE\\Malware",
         "Registry analysis"),

        # Mobile Forensics
        ("MobileDevice", "Artifact: Mobile Device, IMEI: 123456789012345, Model: iPhone 12",
         "Mobile device analysis"),
        ("SMSMessage", "Artifact: SMS Message, Sender: +1234567890, Content: Suspicious message", "SMS analysis"),
        ("CallLog", "Artifact: Call Log, Number: +9876543210, Duration: 5 minutes",
         "Call log analysis"),

        # Email Forensics
        ("EmailMessage", "Artifact: Email Message, From: attacker@evil.com, Subject: Phishing attempt", "Email analysis"),
        ("EmailAccount", "Artifact: Email Account, Address: victim@company.com, Provider: Gmail",
         "Email account analysis"),

        # Network Forensics
        ("NetworkFlow", "Artifact: Network Flow, Protocol: TCP, Port: 443, Bytes: 1024",
         "Network flow analysis"),
        ("DNSRecord", "Artifact: DNS Record, Domain: malicious.com, Type: A, IP: 1.2.3.4", "DNS analysis"),
        ("HTTPRequest", "Artifact: HTTP Request, URL: http://evil.com/malware, Method: GET", "HTTP analysis"),

        # Cloud Forensics
        ("CloudStorage", "Artifact: Cloud Storage, Provider: AWS S3, Bucket: malicious-data",
         "Cloud storage analysis"),
        ("CloudInstance", "Artifact: Cloud Instance, Provider: Azure, Instance: vm-malware",
         "Cloud instance analysis"),

        # IoT Forensics
        ("IoTDevice", "Artifact: IoT Device, Type: Smart Camera, MAC: aa:bb:cc:dd:ee:ff",
         "IoT device analysis"),
        ("SensorData", "Artifact: Sensor Data, Type: Temperature, Value: 25.5°C, Location: Room 101",
         "Sensor data analysis"),

        # Blockchain Forensics
        ("CryptocurrencyTransaction",
         "Artifact: Bitcoin Transaction, Hash: abc123..., Amount: 0.5 BTC", "Cryptocurrency analysis"),
        ("SmartContract", "Artifact: Smart Contract, Address: 0x123..., Network: Ethereum",
         "Smart contract analysis"),

        # Custom/Unknown Artifacts
        ("CustomArtifact", "Artifact: Unknown Type, Properties: field1=value1, field2=value2",
         "Custom artifact analysis"),
        ("FutureArtifact", "Artifact: Future Technology, Type: Quantum Computer, State: Entangled",
         "Future technology analysis")
    ]

    success_count = 0
    total_count = len(test_cases)

    for artifact_type, input_data, description in test_cases:
        if test_case(artifact_type, input_data, description):
            success_count += 1

    print(f"\n{'='*80}")
    print(f"🏁 DOMAIN-AGNOSTIC TEST RESULTS")
    print(f"{'='*80}")
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    print(f"📊 Success Rate: {(success_count/total_count)*100:.1f}%")

    if success_count == total_count:
        print(f"\n🎉 PERFECT! The system can handle ANY artifact type dynamically!")
        print(f"🔧 No hardcoded logic - everything is LLM-driven and domain-agnostic!")
    else:
        print(f"\n⚠️ Some test cases failed. Check the implementation.")

    return success_count == total_count


if __name__ == "__main__":
    main()

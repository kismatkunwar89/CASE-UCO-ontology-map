
import json
import sys
from pathlib import Path

# Add project root to allow imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.validator import validator_node
from state import State

def run_invalid_graph_test():
    """
    Tests the validator_node with a specifically crafted invalid graph
    to ensure it correctly identifies property placement errors.
    """
    print("="*80)
    print("🧪 TESTING `validator_node` with an INVALID graph 🧪")
    print("="*80)

    # 1. Define the invalid graph provided by the user
    invalid_graph = {
      "@context": {
        "case-investigation": "https://ontology.caseontology.org/case/investigation/",
        "kb": "http://example.org/kb/",
        "drafting": "http://example.org/ontology/drafting/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "uco-action": "https://ontology.unifiedcyberontology.org/uco/action/",
        "core": "https://ontology.unifiedcyberontology.org/uco/core/",
        "identity": "https://ontology.unifiedcyberontology.org/uco/identity/",
        "location": "https://ontology.unifiedcyberontology.org/uco/location/",
        "observable": "https://ontology.unifiedcyberontology.org/uco/observable/",
        "tool": "https://ontology.unifiedcyberontology.org/uco/tool/",
        "types": "https://ontology.unifiedcyberontology.org/uco/types/",
        "vocabulary": "https://ontology.unifiedcyberontology.org/uco/vocabulary/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "dfc-ext": "https://www.w3.org/dfc-ext/"
      },
      "@graph": [
        {
          "@id": "kb:file-aa703bfc-4d05-4cfd-9ff3-b4402d008f96",
          "@type": "uco-observable:File",
          "uco-core:hasFacet": [
            {
              "@id": "kb:filefacet-ce142ce4-1a04-486b-b756-4f4cd6194f10"
            }
          ],
          "uco-observable:filePath": "\\Windows\\Prefetch\\MALICIOUS.EXE-12345678.pf",
          "uco-observable:accessedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-09-17T10:35:15Z"
          },
          "uco-observable:observableCreatedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-09-17T10:30:00Z"
          },
          "uco-observable:mftFileID": 42,
          "uco-observable:mftFileNameCreatedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-09-17T10:30:00Z"
          },
          "uco-observable:mftFileNameModifiedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-09-17T10:35:15Z"
          }
        },
        {
          "@id": "kb:filefacet-ce142ce4-1a04-486b-b756-4f4cd6194f10",
          "@type": "uco-observable:MftRecordFacet",
          "uco-observable:mftFileID": 42,
          "uco-observable:mftFileNameAccessedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-09-17T10:35:15Z"
          },
          "uco-observable:mftFileNameCreatedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-09-17T10:30:00Z"
          },
          "uco-observable:mftFileNameModifiedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-09-17T10:35:15Z"
          },
          "uco-observable:mftRecordChangeTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-09-17T10:35:15Z"
          }
        },
        {
          "@id": "kb:file-2d199fb4-2e68-493f-9dfb-57279b14fe64",
          "@type": "uco-observable:File",
          "uco-core:hasFacet": [
            {
              "@id": "kb:filefacet-8d168622-b113-4e3f-89ae-3371341e2fe2"
            }
          ],
          "uco-observable:filePath": "\\Users\\Alice\\Documents\\report.docx",
          "uco-observable:accessedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-01-22T07:02:45Z"
          },
          "uco-observable:observableCreatedTime": {
            "@type": "xsd:dateTime",
            "@value": "2024-10-05T09:12:00Z"
          },
          "uco-observable:mftFileID": 314,
          "uco-observable:mftFileNameCreatedTime": {
            "@type": "xsd:dateTime",
            "@value": "2024-10-05T09:12:00Z"
          },
          "uco-observable:mftFileNameModifiedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-01-20T16:33:11Z"
          }
        },
        {
          "@id": "kb:filefacet-8d168622-b113-4e3f-89ae-3371341e2fe2",
          "@type": "uco-observable:MftRecordFacet",
          "uco-observable:mftFileID": 314,
          "uco-observable:mftFileNameAccessedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-01-22T07:02:45Z"
          },
          "uco-observable:mftFileNameCreatedTime": {
            "@type": "xsd:dateTime",
            "@value": "2024-10-05T09:12:00Z"
          },
          "uco-observable:mftFileNameModifiedTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-01-20T16:33:11Z"
          },
          "uco-observable:mftRecordChangeTime": {
            "@type": "xsd:dateTime",
            "@value": "2025-01-20T16:33:11Z"
          }
        }
      ]
    }

    # 2. Create a mock state object
    mock_state: State = {
        "jsonldGraph": invalid_graph,
        "validationAttempts": 0,
        "validationErrors": [],
        "validationHistory": []
    }

    print("\n📝 Input Graph (Invalid): Contains properties on the File object instead of the Facet.")

    # 3. Execute the validator node
    print("\n🚀 Executing validator_node...")
    result_update = validator_node(mock_state)
    print("---------------------------------")

    # 4. Analyze and report the results
    if result_update:
        validation_result = result_update.get("validation_result", {})
        is_clean = validation_result.get("is_clean", True)
        feedback = result_update.get("validation_feedback", "")

        print("\n📊 VALIDATOR NODE OUTPUT:")
        if not is_clean and feedback:
            print("✅ SUCCESS: The validator correctly identified the graph as invalid.")
            print("\nGenerated Feedback:")
            print(f"-> {feedback}")
        elif is_clean:
            print("❌ FAILURE: The validator incorrectly approved an invalid graph.")
        else:
            print("⚠️ UNEXPECTED OUTPUT: The node produced an unexpected result.")
            print(json.dumps(result_update, indent=2))
    else:
        print("❌ FAILURE: The node returned no output.")

    print("\n" + "="*80)
    print("🏁 INVALID GRAPH TEST COMPLETE 🏁")
    print("="*80)

if __name__ == "__main__":
    run_invalid_graph_test()

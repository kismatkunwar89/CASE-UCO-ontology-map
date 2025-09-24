#!/usr/bin/env python3
"""
Directly call the production agent function with test data
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def run_direct_agent():
    """Run the agent directly by importing and calling the function"""

    print("🤖 RUNNING PRODUCTION AGENT DIRECTLY")
    print("=" * 60)

    # Load test data
    with open('../test.json', 'r') as f:
        test_data = json.load(f)

    print(f"\n📋 INPUT DATA:")
    print(f"Artifact Type: {test_data.get('artifact_type', 'Unknown')}")
    print(f"Description: {test_data.get('description', 'No description')}")

    try:
        # Import the agent function directly
        from agents.ontology_researcher import ontology_research_node
        from state import State

        # Create the state
        state = State(
            rawInputJSON=test_data,
            inputFormat="json",
            messages=[],
            ontologyMap={},
            customFacets={},
            customState={},
            ontologyMarkdown="",
            validation_feedback="",
            validationHistory=[],
            learningContext="",
            memory_context="",
            layer2_feedback_history=[],
            jsonldGraph="",
            uuidPlan=[],
            uuidPlanRelations={}
        )

        print(f"\n🔍 RUNNING AGENT FUNCTION...")

        # Call the agent function
        result = ontology_research_node(state)

        print(f"\n✅ AGENT EXECUTION COMPLETED")
        print(f"Result type: {type(result)}")

        # Extract the markdown report from the result
        if hasattr(result, 'update') and result.update:
            ontology_markdown = result.update.get('ontologyMarkdown', '')
            if ontology_markdown:
                print(
                    f"\n📄 GENERATED REPORT LENGTH: {len(ontology_markdown)} characters")

                # Save the report
                with open('direct_agent_report.md', 'w') as f:
                    f.write(ontology_markdown)

                print(f"✅ Report saved to: direct_agent_report.md")

                # Show a preview of the report
                print(f"\n📋 REPORT PREVIEW:")
                print("-" * 40)
                lines = ontology_markdown.split('\n')
                for i, line in enumerate(lines[:20]):  # Show first 20 lines
                    print(f"{i+1:2d}: {line}")
                if len(lines) > 20:
                    print(f"... ({len(lines) - 20} more lines)")
            else:
                print("❌ No ontology markdown found in result")
                print(f"Available keys: {list(result.update.keys())}")
        else:
            print("❌ No update found in result")
            print(f"Result: {result}")

    except Exception as e:
        print(f"❌ ERROR running agent: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_direct_agent()

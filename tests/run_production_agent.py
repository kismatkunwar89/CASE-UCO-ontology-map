#!/usr/bin/env python3
"""
Run the actual production ontology research agent with test data
"""

import requests
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


def run_production_agent():
    """Run the actual production agent via API call"""

    print("🤖 RUNNING PRODUCTION ONTOLOGY RESEARCH AGENT")
    print("=" * 60)

    # Load test data
    with open('../test.json', 'r') as f:
        test_data = json.load(f)

    print(f"\n📋 INPUT DATA:")
    print(f"Artifact Type: {test_data.get('artifact_type', 'Unknown')}")
    print(f"Description: {test_data.get('description', 'No description')}")

    # Make API call to the production agent
    print(f"\n🔍 CALLING PRODUCTION AGENT API...")

    try:
        # Call the streaming analysis endpoint
        response = requests.post(
            "http://localhost:8000/invoke-streaming",
            json={
                "user_identifier": "test_user",
                "input_artifacts": test_data
            },
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minutes timeout
        )

        if response.status_code == 200:
            print(f"\n✅ AGENT API CALL SUCCESSFUL")

            # Get the response content
            result = response.text
            print(f"📄 RESPONSE LENGTH: {len(result)} characters")

            # Save the report
            with open('production_agent_report.md', 'w') as f:
                f.write(result)

            print(f"✅ Report saved to: production_agent_report.md")

            # Show a preview of the report
            print(f"\n📋 REPORT PREVIEW:")
            print("-" * 40)
            lines = result.split('\n')
            for i, line in enumerate(lines[:20]):  # Show first 20 lines
                print(f"{i+1:2d}: {line}")
            if len(lines) > 20:
                print(f"... ({len(lines) - 20} more lines)")

        else:
            print(f"❌ API CALL FAILED: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to the production agent API")
        print("Make sure the production agent is running on localhost:8000")
        print("Start it with: python main.py")
    except Exception as e:
        print(f"❌ ERROR calling production agent: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_production_agent()

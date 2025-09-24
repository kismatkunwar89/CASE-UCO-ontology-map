# test/test_tool_direct.py
import json
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tools import validate_case_jsonld

def main():
    """
    This test directly invokes the validate_case_jsonld tool with the
    problematic JSON to isolate the source of the validation error.
    """
    print("="*80)
    print("🧪 DIRECTLY TESTING `validate_case_jsonld` TOOL 🧪")
    print("="*80)

    # 1. Load the JSON content from the file
    try:
        with open("test/test.json", "r") as f:
            json_content_str = f.read()
        print("✅ Successfully loaded test/test.json")
    except Exception as e:
        print(f"❌ Failed to load test/test.json: {e}")
        return

    # 2. Invoke the tool directly
    print("\n🚀 Invoking the `validate_case_jsonld` tool...")
    # The tool expects a string containing the JSON data
    result_str = validate_case_jsonld.invoke({
        "input_data": json_content_str
    })
    print("---------------------------------")

    # 3. Print the raw output from the tool
    print("\n📊 RAW OUTPUT FROM TOOL:")
    print(result_str)
    print("---------------------------------")

    # 4. Analyze the result
    print("\n🔬 ANALYSIS:")
    if "Conforms: False" in result_str or "Error" in result_str:
        print("✅ CONCLUSION: The `validate_case_jsonld` tool IS correctly identifying an error.")
        print("   This confirms the failure originates from the tool itself due to the semantically invalid graph.")
    elif "Conforms: True" in result_str:
        print("❌ CONCLUSION: The `validate_case_jsonld` tool is NOT catching the error.")
        print("   This means the failure happens later in the `validator_node`'s logic (likely the LLM call).")
    else:
        print("⚠️  UNKNOWN: The tool returned an unexpected result.")

    print("\n" + "="*80)
    print("🏁 DIRECT TOOL TEST COMPLETE 🏁")
    print("="*80)

if __name__ == "__main__":
    main()

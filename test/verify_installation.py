#!/usr/bin/env python3
"""
Simple verification script to check if the Forensic Agent System is properly installed.
Run this after installing dependencies to verify everything works.
"""

import sys
import os


def test_imports():
    """Test all required imports."""
    print("🧪 Testing imports...")

    required_modules = [
        ("langchain", "LangChain core"),
        ("langchain_core", "LangChain core components"),
        ("langchain_openai", "OpenAI integration"),
        ("langgraph", "LangGraph workflow engine"),
        ("openai", "OpenAI API client"),
        ("requests", "HTTP requests"),
        ("bs4", "BeautifulSoup HTML parsing"),
        ("pydantic", "Data validation"),
        ("rdflib", "RDF processing"),
        ("tqdm", "Progress bars"),
        ("phoenix.otel", "Phoenix tracing")
    ]

    failed_imports = []

    for module, description in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError as e:
            print(f"❌ {module} - {description}: {e}")
            failed_imports.append(module)

    return len(failed_imports) == 0


def test_agent_imports():
    """Test agent-specific imports."""
    print("\n🤖 Testing agent imports...")

    try:
        from agents.graph_generator import graph_generator_node
        print("✅ Graph generator agent")
    except ImportError as e:
        print(f"❌ Graph generator agent: {e}")
        return False

    try:
        from agents.supervisor import supervisor_node
        print("✅ Supervisor agent")
    except ImportError as e:
        print(f"❌ Supervisor agent: {e}")
        return False

    try:
        from agents.validator import validator_node
        print("✅ Validator agent")
    except ImportError as e:
        print(f"❌ Validator agent: {e}")
        return False

    try:
        from tools import generate_uuid
        print("✅ UUID generation tool")
    except ImportError as e:
        print(f"❌ UUID generation tool: {e}")
        return False

    return True


def test_environment():
    """Test environment configuration."""
    print("\n🔧 Testing environment...")

    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("✅ OPENAI_API_KEY is set")
        return True
    else:
        print("⚠️  OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return False


def main():
    """Main verification function."""
    print("🔍 Forensic Agent System - Installation Verification")
    print("=" * 60)

    # Test basic imports
    imports_ok = test_imports()

    # Test agent imports
    agents_ok = test_agent_imports()

    # Test environment
    env_ok = test_environment()

    print("\n" + "=" * 60)
    print("📊 VERIFICATION RESULTS:")
    print(f"   Dependencies: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Agents: {'✅ PASS' if agents_ok else '❌ FAIL'}")
    print(f"   Environment: {'✅ PASS' if env_ok else '⚠️  WARN'}")

    if imports_ok and agents_ok:
        print("\n🎉 INSTALLATION SUCCESSFUL!")
        print("✅ All dependencies are properly installed")
        print("✅ All agents can be imported")
        if env_ok:
            print("✅ Environment is configured")
            print("\n🚀 You can now run: python main.py")
        else:
            print("⚠️  Set OPENAI_API_KEY to use the system")
            print("\n🚀 You can still run: python main.py")
            print("   (but you'll need to set the API key first)")
    else:
        print("\n❌ INSTALLATION ISSUES DETECTED")
        print("Please check the error messages above and:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Create virtual environment if needed: python -m venv venv")
        print("3. Activate virtual environment: source venv/bin/activate")

    return imports_ok and agents_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

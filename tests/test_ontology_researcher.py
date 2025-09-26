"""Utility script to exercise the ontology researcher node.

Run with:
    OPENAI_API_KEY=... PYTHONPATH=. python tests/test_ontology_researcher.py

This mirrors the behaviour we used while developing prompts without
requiring pytest or extra harness code.
"""
import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from agents.ontology_researcher import ontology_research_step_node
from state import State

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "windows_prefetch.json"


def load_fixture() -> dict:
    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return {
        "artifact_type": "Windows Prefetch execution cache records",
        "description": "Investigator-supplied host telemetry summarising executable launch traces in a neutral structure.",
        "source": "Structured JSON export from enterprise endpoint monitoring workflow.",
        "records": records,
        "observations": records,
    }


def run() -> None:
    payload = load_fixture()
    initial_state = State(
        messages=[HumanMessage(content=json.dumps(payload, ensure_ascii=False))],
        rawInputJSON=payload,
    )

    result_state = ontology_research_step_node(initial_state)
    markdown = result_state.get("ontologyMarkdown")
    if markdown:
        print(markdown)
    else:
        print(json.dumps(result_state, indent=2))


if __name__ == "__main__":
    run()

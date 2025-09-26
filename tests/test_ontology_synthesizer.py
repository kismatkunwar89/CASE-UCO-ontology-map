"""Utility script to exercise the ontology researcher + synthesizer path.

Run with:
    OPENAI_API_KEY=... PYTHONPATH=. python tests/test_ontology_synthesizer.py
"""
import json
from pathlib import Path

from langchain_core.messages import HumanMessage

from agents.ontology_researcher import ontology_research_step_node
from agents.ontology_synthesizer import ontology_synthesis_node
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
    state = State(
        messages=[HumanMessage(content=json.dumps(payload, ensure_ascii=False))],
        rawInputJSON=payload,
    )

    state = ontology_research_step_node(state)
    markdown = state.get("ontologyMarkdown")
    if markdown:
        print("--- Ontology Markdown ---")
        print(markdown)

    synthesis = ontology_synthesis_node(state)
    state.update(synthesis)
    ontology_map = state.get("ontologyMap")
    if ontology_map:
        print("--- Synthesized JSON ---")
        print(json.dumps(ontology_map, indent=2))
    else:
        print(json.dumps(synthesis, indent=2))


if __name__ == "__main__":
    run()

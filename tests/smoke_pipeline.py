"""Manual smoke-test script for the ontology workflow.

Run with:
    OPENAI_API_KEY=... PYTHONPATH=. python tests/smoke_pipeline.py

This script exercises the researcher -> synthesizer -> UUID planner -> graph
pipeline using a deterministic fixture. It mirrors the tests used during
prompt development but keeps dependencies optional (no pytest required).
"""
import json
from pathlib import Path

from langchain_core.messages import HumanMessage

import agents.ontology_researcher as research_module
import agents.ontology_synthesizer as synth_module
import agents.uuid_planner as planner_module
from agents.ontology_researcher import ontology_research_step_node
from agents.ontology_synthesizer import ontology_synthesis_node
from agents.uuid_planner import uuid_planner_node
from agents.graph_generator import graph_generator_node
from state import State

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "windows_prefetch.json"


def load_fixture() -> list[dict]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_state() -> State:
    records = load_fixture()
    payload = {
        "artifact_type": "Windows Prefetch execution cache records",
        "description": "Investigator-supplied host telemetry summarising executable launch traces in a neutral structure.",
        "source": "Structured JSON export from enterprise endpoint monitoring workflow.",
        "records": records,
        "observations": records,
    }
    return State(messages=[HumanMessage(content=json.dumps(payload))], rawInputJSON=payload)


def run_pipeline() -> None:
    state = build_state()

    print("[stage] ontology_research_step_node")
    state = ontology_research_step_node(state)

    print("[stage] ontology_synthesis_node")
    synth_result = ontology_synthesis_node(state)
    state.update(synth_result)

    # Restore raw input so the planner sees the evidence
    state["rawInputJSON"] = build_state().get("rawInputJSON")

    print("[stage] uuid_planner_node")
    alias_injections = {
        "sourcefilename": ["applicationFileName", "fileName", "filePath", "accessedFile"],
        "referencedpaths": ["accessedDirectory", "accessedFile"],
        "runcount": ["timesExecuted"],
        "filecreatedtime": ["firstRun"],
        "filemodifiedtime": ["lastRun"],
        "volumeserialnumber": ["volume"],
    }
    original_alias_map = {k: list(v) for k, v in planner_module.PROPERTY_ALIAS_MAP.items()}
    try:
        for key, values in alias_injections.items():
            planner_module.PROPERTY_ALIAS_MAP.setdefault(key, [])
            for value in values:
                if value not in planner_module.PROPERTY_ALIAS_MAP[key]:
                    planner_module.PROPERTY_ALIAS_MAP[key].append(value)
        planner_output = uuid_planner_node(state)
    finally:
        planner_module.PROPERTY_ALIAS_MAP = {k: values for k, values in original_alias_map.items()}

    state.update(planner_output)
    print(json.dumps({
        "uuidPlan": state.get("uuidPlan"),
        "slotTypeMap": state.get("slotTypeMap"),
    }, indent=2))

    print("[stage] graph_generator_node")
    graph_output = graph_generator_node(state)
    # Print only the JSON-LD graph, not the messages
    print("Generated JSON-LD Graph:")
    print(json.dumps(graph_output.get("jsonldGraph"), indent=2))


if __name__ == "__main__":
    run_pipeline()

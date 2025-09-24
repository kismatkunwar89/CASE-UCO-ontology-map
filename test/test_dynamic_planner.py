import pytest
from agents.uuid_planner import uuid_planner_node
from state import State
from tools import _generate_record_fingerprint, _uuid5, NS_RECORD, NS_SLOT

def test_determinism():
    """Tests that the planner produces identical plans for identical inputs."""
    sample_records = [
        {"name": "record1", "value": "A"},
        {"name": "record2", "value": "B"}
    ]
    sample_ontology_map = {
        "classes": ["File"],
        "facets": ["FileFacet"],
        "properties": {
            "FileFacet": ["name", "value"]
        }
    }

    initial_state = {
        "rawInputJSON": sample_records,
        "ontologyMap": sample_ontology_map,
        "uuidPlan": None # Ensure planner runs
    }

    # First run
    result1 = uuid_planner_node(initial_state)

    # Second run with identical state
    result2 = uuid_planner_node(initial_state)

    # Assert that the results are identical
    assert result1["uuidPlan"] == result2["uuidPlan"]
    assert result1["slotTypeMap"] == result2["slotTypeMap"]
    assert result1["recordFingerprints"] == result2["recordFingerprints"]

def test_incremental_add():
    """Tests that adding a record only adds to the plan."""
    # Initial state with one record
    initial_records = [{"name": "record1", "value": "A"}]
    sample_ontology_map = {
        "classes": ["File"], "facets": ["FileFacet"],
        "properties": {"FileFacet": ["name", "value"]}
    }
    initial_state = {
        "rawInputJSON": initial_records, "ontologyMap": sample_ontology_map, "uuidPlan": None
    }
    result1 = uuid_planner_node(initial_state)
    
    # New state with an added record
    added_records = initial_records + [{"name": "record2", "value": "B"}]
    next_state = {
        "rawInputJSON": added_records, "ontologyMap": sample_ontology_map,
        "uuidPlan": result1["uuidPlan"], # Pass previous plan
        "recordFingerprints": result1["recordFingerprints"],
        "slotTypeMap": result1["slotTypeMap"]
    }
    result2 = uuid_planner_node(next_state)

    assert len(result2["uuidPlan"]) == 2
    # The first plan row should be identical
    assert result1["uuidPlan"][0] == result2["uuidPlan"][0]

def test_incremental_update():
    """Tests that updating a record changes only its part of the plan."""
    # Initial state with two records
    initial_records = [{"name": "record1", "value": "A"}, {"name": "record2", "value": "B"}]
    sample_ontology_map = {
        "classes": ["File"], "facets": ["FileFacet"],
        "properties": {"FileFacet": ["name", "value"]}
    }
    initial_state = {
        "rawInputJSON": initial_records, "ontologyMap": sample_ontology_map, "uuidPlan": None
    }
    result1 = uuid_planner_node(initial_state)
    
    # New state with one record updated
    updated_records = [{"name": "record1", "value": "A_changed"}, {"name": "record2", "value": "B"}]
    next_state = {
        "rawInputJSON": updated_records, "ontologyMap": sample_ontology_map,
        "uuidPlan": result1["uuidPlan"],
        "recordFingerprints": result1["recordFingerprints"],
        "slotTypeMap": result1["slotTypeMap"]
    }
    result2 = uuid_planner_node(next_state)

    assert len(result2["uuidPlan"]) == 2
    # The first plan row should be different
    assert result1["uuidPlan"][0] != result2["uuidPlan"][0]
    # The second plan row should be identical
    assert result1["uuidPlan"][1] == result2["uuidPlan"][1]

def test_incremental_delete():
    """Tests that deleting a record removes it from the plan."""
    # Initial state with two records
    initial_records = [{"name": "record1", "value": "A"}, {"name": "record2", "value": "B"}]
    sample_ontology_map = {
        "classes": ["File"], "facets": ["FileFacet"],
        "properties": {"FileFacet": ["name", "value"]}
    }
    initial_state = {
        "rawInputJSON": initial_records, "ontologyMap": sample_ontology_map, "uuidPlan": None
    }
    result1 = uuid_planner_node(initial_state)
    
    # New state with one record deleted
    deleted_records = [{"name": "record2", "value": "B"}]
    next_state = {
        "rawInputJSON": deleted_records, "ontologyMap": sample_ontology_map,
        "uuidPlan": result1["uuidPlan"],
        "recordFingerprints": result1["recordFingerprints"],
        "slotTypeMap": result1["slotTypeMap"]
    }
    result2 = uuid_planner_node(next_state)

    assert len(result2["uuidPlan"]) == 1
    # The remaining plan row should be the one for the second record
    assert result1["uuidPlan"][1] == result2["uuidPlan"][0]

def test_ontology_change():
    """Tests that changing the ontology triggers a re-plan."""
    # Initial state with one record and a simple ontology
    initial_records = [{"name": "record1", "size": 123}]
    initial_ontology_map = {
        "classes": ["File"], "facets": [],
        "properties": {"File": ["name"]}
    }
    initial_state = {
        "rawInputJSON": initial_records, "ontologyMap": initial_ontology_map, "uuidPlan": None
    }
    result1 = uuid_planner_node(initial_state)
    
    # The initial plan should not have a size-related facet
    assert "sizefacet" not in result1["uuidPlan"][0]

    # New state with an updated ontology that now recognizes the 'size' property
    updated_ontology_map = {
        "classes": ["File"], "facets": ["SizeFacet"],
        "properties": {"File": ["name"], "SizeFacet": ["size"]}
    }
    # In a real run, an ontology change would invalidate the plan. We simulate that here.
    next_state = {
        "rawInputJSON": initial_records, "ontologyMap": updated_ontology_map, "uuidPlan": None
    }
    
    result2 = uuid_planner_node(next_state)

    assert len(result2["uuidPlan"]) == 1
    # The new plan should be different and contain the new facet
    assert result1["uuidPlan"][0] != result2["uuidPlan"][0]
    assert "sizefacet" in result2["uuidPlan"][0]

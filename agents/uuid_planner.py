
from state import State
from tools import plan_record_uuids


def uuid_planner_node(state: State) -> dict:
    """
    Generates a deterministic UUID plan for all records if one does not already exist.
    This ensures that UUIDs remain stable across correction loops unless explicitly invalidated.
    """
    # If a plan already exists, do nothing.
    if state.get("uuidPlan"):
        print("[INFO] [UUID Planner] UUID plan already exists. Skipping.")
        return {}

    print("[INFO] [UUID Planner] No UUID plan found. Generating a new one.")

    # The number of records to process is determined by the original input.
    raw_input = state.get("rawInputJSON", {})
    record_count = 0

    # Handle different input formats
    if isinstance(raw_input, list):
        # Input is directly a list of records
        record_count = len(raw_input)
        print(
            f"[INFO] [UUID Planner] Found {record_count} records in list format")
    elif isinstance(raw_input, dict):
        if "records" in raw_input and isinstance(raw_input["records"], list):
            # Input has a "records" key
            record_count = len(raw_input["records"])
            print(
                f"[INFO] [UUID Planner] Found {record_count} records in records key")
        elif len(raw_input) > 0:
            # Single record as dict
            record_count = 1
            print(f"[INFO] [UUID Planner] Found 1 record in dict format")
        else:
            record_count = 0
            print(f"[INFO] [UUID Planner] Empty dict input")
    else:
        record_count = 0
        print(f"[INFO] [UUID Planner] Non-dict/list input: {type(raw_input)}")

    # If no records found, return None to indicate no plan needed
    if record_count == 0:
        print("[WARNING] [UUID Planner] No records found in rawInputJSON to plan for.")
        return {"uuidPlan": None}

    # Extract class and facet slugs for planning. We use the direct names as slugs.
    ontology_map = state.get("ontologyMap", {})
    class_slugs = ontology_map.get("classes", [])
    facet_slugs = ontology_map.get("facets", [])

    # Generate the plan using the helper from tools.py
    try:
        plan = plan_record_uuids(
            record_count=record_count,
            class_slugs=class_slugs,
            facet_slugs=facet_slugs
        )
        print(
            f"[SUCCESS] [UUID Planner] Generated plan for {record_count} records.")
        return {"uuidPlan": plan}
    except Exception as e:
        print(f"[ERROR] [UUID Planner] Failed to generate UUID plan: {e}")
        # Return an error state or handle it as per design
        return {"graphGeneratorErrors": [f"Failed to generate UUID plan: {e}"]}


def invalidate_uuid_plan_node(state: State) -> dict:
    """
    A simple node that clears the UUID plan from the state, forcing regeneration.
    This is called when an ID-related validation error is detected.
    """
    print("[INFO] [UUID Invalidator] Invalidating UUID plan due to ID-related feedback.")
    return {"uuidPlan": None}

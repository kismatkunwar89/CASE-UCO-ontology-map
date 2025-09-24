from state import State
from tools import _generate_record_fingerprint, _uuid5, NS_RECORD, NS_SLOT

def uuid_planner_node(state: State) -> dict:
    """
    Generates a deterministic UUID plan for all records. 
    This version is incremental, using content-based fingerprints to re-plan only
    new or changed records.
    """
    print("[INFO] [UUID Planner] Running incremental planner...")

    # --- Get current and previous state ---
    raw_input = state.get("rawInputJSON", [])
    records = raw_input if isinstance(raw_input, list) else ([raw_input] if raw_input else [])
    
    previous_plan = state.get("uuidPlan") or []
    previous_fingerprints = state.get("recordFingerprints") or []
    previous_map = state.get("slotTypeMap", {})
    
    if not records:
        print("[WARNING] [UUID Planner] No records found in rawInputJSON to plan for.")
        return {"uuidPlan": [], "slotTypeMap": {}, "recordFingerprints": []}

    # --- Fingerprint Calculation ---
    current_fingerprints = [_generate_record_fingerprint(rec) for rec in records]
    
    # --- Incremental Planning ---
    new_plan = []
    new_map = {}
    old_plan_map = {fp: plan for fp, plan in zip(previous_fingerprints, previous_plan)}

    ontology_map = state.get("ontologyMap", {})
    all_class_slugs = [c.lower() for c in ontology_map.get("classes", [])]
    all_facet_slugs = [f.lower() for f in ontology_map.get("facets", [])]
    prop_to_owner = {prop.lower(): owner.lower() for owner, props in ontology_map.get("properties", {}).items() for prop in props}

    for i, fingerprint in enumerate(current_fingerprints):
        if fingerprint in old_plan_map:
            # UNCHANGED: Reuse the old plan and map entries
            plan_row = old_plan_map[fingerprint]
            new_plan.append(plan_row)
            for slot_uuid in plan_row.values():
                if slot_uuid in previous_map:
                    new_map[slot_uuid] = previous_map[slot_uuid]
        else:
            # NEW OR CHANGED: Generate a new plan row
            record = records[i]
            record_uuid = _uuid5(NS_RECORD, fingerprint)
            plan_row = {}
            required_slots = set()

            for cls in all_class_slugs:
                if any(cls in key.lower() for key in record.keys()):
                    required_slots.add(cls)
            if not required_slots:
                required_slots.add('observableobject')

            for key in record.keys():
                owner = prop_to_owner.get(key.lower())
                if owner and owner in all_facet_slugs:
                    required_slots.add(owner)

            for slot_slug in required_slots:
                slot_uuid = _uuid5(NS_SLOT, f"{record_uuid}:{slot_slug}")
                plan_row[slot_slug] = slot_uuid
                original_slug = next((s for s in ontology_map.get("classes", []) + ontology_map.get("facets", []) if s.lower() == slot_slug), slot_slug)
                new_map[slot_uuid] = f"uco-observable:{original_slug}"
            
            if ontology_map.get("relationships"):
                for rel_idx, rel in enumerate(ontology_map["relationships"]):
                    kind = rel.get("type", "related_to").lower()
                    rel_slug = f"relationship_{kind}_{rel_idx}"
                    rel_uuid = _uuid5(NS_SLOT, f"{record_uuid}:{rel_slug}")
                    plan_row[rel_slug] = rel_uuid
                    new_map[rel_uuid] = "uco-observable:ObservableRelationship"
            
            new_plan.append(plan_row)

    print(f"[SUCCESS] [UUID Planner] Generated plan for {len(new_plan)} records.")

    return {
        "recordFingerprints": current_fingerprints,
        "uuidPlan": new_plan,
        "slotTypeMap": new_map,
    }

def invalidate_uuid_plan_node(state: State) -> dict:
    """
    Clears the UUID plan from the state to force regeneration.
    Can perform partial invalidation if `uuids_to_invalidate` is present in the state.
    """
    uuids_to_invalidate = state.get("uuids_to_invalidate")
    if uuids_to_invalidate:
        print(f"[INFO] [UUID Invalidator] Invalidating parts of UUID plan for: {uuids_to_invalidate}")
        current_plan = state.get("uuidPlan", [])
        new_plan = [plan for plan in current_plan if not any(uuid in plan.values() for uuid in uuids_to_invalidate)]
        
        current_map = state.get("slotTypeMap", {})
        new_map = {k: v for k, v in current_map.items() if k not in uuids_to_invalidate}

        return {"uuidPlan": new_plan, "slotTypeMap": new_map, "uuids_to_invalidate": None}
    else:
        print("[INFO] [UUID Invalidator] Invalidating entire UUID plan due to general ID-related feedback.")
        return {"uuidPlan": None, "slotTypeMap": None, "recordFingerprints": None}
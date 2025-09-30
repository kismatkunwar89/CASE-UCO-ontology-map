from collections import OrderedDict
import re
from typing import Dict, Iterable, List, Tuple

from state import State
from tools import _generate_record_fingerprint, _uuid5, NS_RECORD, NS_SLOT
from config import MAX_UUID_PLANNING_ATTEMPTS, MAX_RECORDS_PER_PLAN


PROPERTY_ALIAS_MAP = {
    "entrynumber": ["mftFileID", "entryID"],
    "sequencenumber": ["sequenceNumber", "entrySequence"],
    "parententrynumber": ["mftParentID"],
    "fullpath": ["filePath"],
    "inuse": ["allocationStatus", "isAllocated"],
    "si_created": ["mftFileNameCreatedTime", "createdTime"],
    "si_modified": ["mftFileNameModifiedTime", "modifiedTime"],
    "si_accessed": ["mftFileNameAccessedTime", "accessedTime"],
    "fn_created": ["createdTime"],
    "fn_modified": ["modifiedTime"],
    "size": ["sizeInBytes"],
    "filename": ["fileName"],
    "filesystem": ["fileSystemType"],
}


def _slugify(name: str) -> str:
    return name.replace(" ", "_").replace("-", "_").lower()


def _extract_records(raw_input: object) -> List[Dict]:
    """Normalise the raw input into a list of per-record dictionaries."""

    if isinstance(raw_input, list):
        return [rec for rec in raw_input if isinstance(rec, dict)]

    if isinstance(raw_input, dict):
        records = raw_input.get("records")
        if isinstance(records, list):
            # Fan-out: flatten each record while preserving shared metadata (e.g., description)
            shared = {
                k: v for k, v in raw_input.items()
                if k not in ("records", "record")
            }
            normalised: List[Dict] = []
            for rec in records:
                if isinstance(rec, dict):
                    flattened = {**shared}
                    flattened.update(rec)
                    normalised.append(flattened)
            if normalised:
                return normalised

        # Single-record payloads store evidence under the "record" key; flatten it.
        single_record = raw_input.get("record")
        if isinstance(single_record, dict):
            shared = {
                k: v for k, v in raw_input.items()
                if k not in ("records", "record")
            }
            flattened = {**shared}
            flattened.update(single_record)
            return [flattened]

        return [raw_input] if raw_input else []

    return []


def _choose_primary_class(classes: Iterable[str], facets: Iterable[str]) -> str:
    facet_set = {f.lower() for f in facets}
    for cls in classes:
        if cls.lower() not in facet_set and not cls.lower().endswith("facet"):
            return cls
    return "ObservableObject"


def _iri_for(name: str) -> str:
    # Default to CASE/UCO observable namespace when no explicit mapping is available.
    return f"uco-observable:{name}"


def _normalize_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _tokenize(name: str) -> List[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    spaced = spaced.replace("_", " ").replace("-", " ").replace(":", " ")
    return [tok for tok in spaced.lower().split() if tok]


def _prepare_property_index(ontology_properties: Dict[str, List[str]]) -> Dict[str, List[Tuple[str, set]]]:
    index: Dict[str, List[Tuple[str, set]]] = {}
    for owner, props in ontology_properties.items():
        owner_slug = _slugify(owner)
        entries: List[Tuple[str, set]] = []
        for prop in props:
            entries.append((prop, set(_tokenize(prop))))
        if entries:
            index[owner_slug] = entries
    return index


def _match_property(raw_key: str, owner_property_index: Dict[str, List[Tuple[str, set]]]) -> Tuple[str | None, str | None]:
    alias_candidates = PROPERTY_ALIAS_MAP.get(raw_key)
    if alias_candidates:
        for owner_slug, entries in owner_property_index.items():
            for prop, _ in entries:
                if prop in alias_candidates:
                    return owner_slug, prop
                if prop.lower() in [alias.lower() for alias in alias_candidates]:
                    return owner_slug, prop

    raw_tokens = set(_tokenize(raw_key))
    best_score = 0
    best_owner = None
    best_prop = None
    for owner_slug, entries in owner_property_index.items():
        for prop, tokens in entries:
            score = len(raw_tokens & tokens)
            if score > best_score:
                best_score = score
                best_owner = owner_slug
                best_prop = prop
    if best_score > 0:
        return best_owner, best_prop
    return None, None


def _qualify_property(prop_name: str) -> str:
    if ":" in prop_name:
        return prop_name
    return f"uco-observable:{prop_name}"


def _build_source_property_map(records: List[Dict], plan_rows: List[OrderedDict[str, str]], slot_type_map: Dict[str, str], ontology_map: Dict[str, Dict]) -> Dict[str, Dict[str, Dict]]:
    source_map: Dict[str, Dict[str, Dict]] = {}
    property_index = _prepare_property_index(ontology_map.get("properties", {}))
    property_field_map = (ontology_map.get("additional_details", {}) or {}).get("propertyFieldMap", {})

    for record, plan_row in zip(records, plan_rows):
        if not plan_row:
            continue
        slug_to_uuid = plan_row
        primary_slug = next(iter(plan_row))

        # Ensure every slot has an entry even if no properties map to it
        for slot_slug, slot_uuid in slug_to_uuid.items():
            source_map.setdefault(slot_uuid, {
                "type": slot_type_map.get(slot_uuid, ""),
                "properties": {},
                "raw": {}
            })

        # Apply explicit property mappings from markdown tables first
        if property_field_map:
            for owner, prop_map in property_field_map.items():
                owner_slug = _slugify(owner)
                target_slug = owner_slug if owner_slug in slug_to_uuid else primary_slug
                slot_uuid = slug_to_uuid.get(target_slug)
                if not slot_uuid:
                    continue
                slot_entry = source_map[slot_uuid]
                for prop_name, fields in (prop_map or {}).items():
                    if not fields:
                        continue
                    value = None
                    for field_name in fields:
                        if isinstance(record, dict) and field_name in record and record[field_name] is not None:
                            value = record[field_name]
                            break
                    if value is None:
                        continue
                    qualified = _qualify_property(prop_name)
                    slot_entry["properties"][qualified] = value

        # Fallback heuristic mapping for properties without explicit rows
        for raw_key, value in record.items():
            normalized_key = _normalize_key(raw_key)
            owner_slug, prop_name = _match_property(normalized_key, property_index)

            target_slug = owner_slug if owner_slug in slug_to_uuid else primary_slug
            slot_uuid = slug_to_uuid[target_slug]
            slot_entry = source_map[slot_uuid]
            slot_entry["raw"][raw_key] = value

            if prop_name:
                qualified = _qualify_property(prop_name)
                slot_entry["properties"][qualified] = value

    return source_map


def uuid_planner_node(state: State) -> dict:
    """
    Build a deterministic UUID plan per record using ontology hints.

    GUARDRAILS: Includes attempt limits and record limits to prevent infinite loops and memory exhaustion.
    """
    current_attempts = state.get("uuidPlanningAttempts", 0)

    print(f"[INFO] [UUID Planner] Running incremental planner (attempt {current_attempts + 1}/{MAX_UUID_PLANNING_ATTEMPTS})...")

    #GUARDRAIL: Check max planning attempts
    if current_attempts >= MAX_UUID_PLANNING_ATTEMPTS:
        print(f"[WARNING] [UUID Planner] Max planning attempts ({MAX_UUID_PLANNING_ATTEMPTS}) reached.")
        print("[INFO] [UUID Planner] Using current plan even if imperfect to allow workflow to continue.")
        # Return current plan without incrementing - we're done trying
        current_plan = state.get("uuidPlan") or []
        current_map = state.get("slotTypeMap", {})
        current_fingerprints = state.get("recordFingerprints") or []
        current_source_map = state.get("sourcePropertyMap", {})
        return {
            "uuidPlan": current_plan,
            "slotTypeMap": current_map,
            "recordFingerprints": current_fingerprints,
            "sourcePropertyMap": current_source_map,
            "uuidPlanningAttempts": current_attempts  # Don't increment - we're done
        }

    raw_input = state.get("rawInputJSON")
    records = _extract_records(raw_input)

    previous_plan = state.get("uuidPlan") or []
    previous_fingerprints = state.get("recordFingerprints") or []
    previous_map = state.get("slotTypeMap", {})

    if not records:
        print("[WARNING] [UUID Planner] No records found in rawInputJSON to plan for.")
        return {
            "uuidPlan": [],
            "slotTypeMap": {},
            "recordFingerprints": [],
            "sourcePropertyMap": {},
            "uuidPlanningAttempts": 0  # Reset on no records
        }

    # GUARDRAIL: Limit number of records to prevent memory exhaustion
    if len(records) > MAX_RECORDS_PER_PLAN:
        print(f"[WARNING] [UUID Planner] Too many records ({len(records)}). Limiting to {MAX_RECORDS_PER_PLAN}.")
        records = records[:MAX_RECORDS_PER_PLAN]

    ontology_map = state.get("ontologyMap", {})
    ontology_classes = list(ontology_map.get("classes", []))
    ontology_facets = list(ontology_map.get("facets", []))
    if not ontology_facets:
        for owner in ontology_map.get("properties", {}).keys():
            if owner not in ontology_facets and owner.lower().endswith("facet"):
                ontology_facets.append(owner)
    relationships = ontology_map.get("relationships", []) or []

    primary_class = _choose_primary_class(ontology_classes, ontology_facets)
    if primary_class == "ObservableObject":
        if ontology_classes:
            primary_class = ontology_classes[0]
        else:
            for owner in ontology_map.get("properties", {}).keys():
                if not owner.lower().endswith("facet"):
                    primary_class = owner
                    break
    facet_slugs = [_slugify(facet) for facet in ontology_facets]

    current_fingerprints = [_generate_record_fingerprint(rec) for rec in records]
    old_plan_map = {fp: plan for fp, plan in zip(previous_fingerprints, previous_plan)}

    new_plan: List[OrderedDict[str, str]] = []
    new_map: Dict[str, str] = {}

    for record, fingerprint in zip(records, current_fingerprints):
        if fingerprint in old_plan_map:
            plan_row = OrderedDict(old_plan_map[fingerprint])
            new_plan.append(plan_row)
            for slot_uuid in plan_row.values():
                if slot_uuid in previous_map:
                    new_map[slot_uuid] = previous_map[slot_uuid]
            continue

        record_uuid = _uuid5(NS_RECORD, fingerprint)
        plan_row: "OrderedDict[str, str]" = OrderedDict()

        # Always create a primary object node so downstream generators have a root.
        primary_slug = _slugify(primary_class)
        primary_uuid = _uuid5(NS_SLOT, f"{record_uuid}:{primary_slug}")
        plan_row[primary_slug] = primary_uuid
        new_map[primary_uuid] = _iri_for(primary_class)

        # Add one slot per facet advertised by the ontology map.
        for facet_name, facet_slug in zip(ontology_facets, facet_slugs):
            facet_uuid = _uuid5(NS_SLOT, f"{record_uuid}:{facet_slug}")
            plan_row[facet_slug] = facet_uuid
            new_map[facet_uuid] = _iri_for(facet_name)

        # Relationships (if any) get their own deterministic IDs per record.
        for rel_idx, rel in enumerate(relationships):
            kind = rel.get("type") or "relatedTo"
            rel_slug = _slugify(f"relationship_{kind}_{rel_idx}")
            rel_uuid = _uuid5(NS_SLOT, f"{record_uuid}:{rel_slug}")
            plan_row[rel_slug] = rel_uuid
            new_map[rel_uuid] = _iri_for("ObservableRelationship")

        new_plan.append(plan_row)

    # Ensure slot_type_map contains reused entries as well
    for plan_row in new_plan:
        for slot_uuid in plan_row.values():
            if slot_uuid not in new_map and slot_uuid in previous_map:
                new_map[slot_uuid] = previous_map[slot_uuid]

    source_property_map = _build_source_property_map(records, new_plan, new_map, ontology_map)

    print(f"[SUCCESS] [UUID Planner] Generated plan for {len(new_plan)} records.")

    # Success - reset attempts counter
    return {
        "recordFingerprints": current_fingerprints,
        "uuidPlan": new_plan,
        "slotTypeMap": new_map,
        "sourcePropertyMap": source_property_map,
        "uuidPlanningAttempts": 0  # Reset on successful planning
    }

def invalidate_uuid_plan_node(state: State) -> dict:
    """
    Clears the UUID plan from the state to force regeneration.
    Can perform partial invalidation if `uuids_to_invalidate` is present in the state.

    GUARDRAILS: Increments planning attempt counter to prevent infinite invalidation loops.
    """
    current_attempts = state.get("uuidPlanningAttempts", 0)

    print(f"[INFO] [UUID Invalidator] Invalidation attempt {current_attempts + 1}/{MAX_UUID_PLANNING_ATTEMPTS}")

    # GUARDRAIL: If we've reached max attempts, don't invalidate - use what we have
    if current_attempts >= MAX_UUID_PLANNING_ATTEMPTS:
        print(f"[WARNING] [UUID Invalidator] Max planning attempts reached. Skipping invalidation.")
        print("[INFO] [UUID Invalidator] Proceeding with current plan to avoid infinite loop.")
        return {
            "uuids_to_invalidate": None,  # Clear the invalidation request
            "uuidPlanningAttempts": current_attempts  # Keep counter as-is
        }

    uuids_to_invalidate = state.get("uuids_to_invalidate")
    if uuids_to_invalidate:
        print(f"[INFO] [UUID Invalidator] Invalidating parts of UUID plan for: {uuids_to_invalidate}")
        current_plan = state.get("uuidPlan", [])
        new_plan = [plan for plan in current_plan if not any(uuid in plan.values() for uuid in uuids_to_invalidate)]

        current_map = state.get("slotTypeMap", {})
        new_map = {k: v for k, v in current_map.items() if k not in uuids_to_invalidate}

        return {
            "uuidPlan": new_plan,
            "slotTypeMap": new_map,
            "uuids_to_invalidate": None,
            "uuidPlanningAttempts": current_attempts + 1  # Increment on invalidation
        }
    else:
        print("[INFO] [UUID Invalidator] Invalidating entire UUID plan due to general ID-related feedback.")
        return {
            "uuidPlan": None,
            "slotTypeMap": None,
            "recordFingerprints": None,
            "uuidPlanningAttempts": current_attempts + 1  # Increment on invalidation
        }

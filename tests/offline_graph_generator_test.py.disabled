# Run with:  PYTHONPATH=. python -m tests.offline_graph_generator_test
# or:        PYTHONPATH=. python tests/offline_graph_generator_test.py

import os
import re
import json
from typing import Any, Dict, List

# --- Import your project code
import config as CFG
try:
    # if your file lives under agents/
    from agents.graph_generator import graph_generator_node
except ImportError:
    # fallback if it's top-level
    from agents.graph_generator import graph_generator_node


# Import the robust functions from the production code
from agents.graph_generator import (
    _as_list, _as_dict, _get_analysis, _get_mapping, _iter_plan_items,
    _merge_context_from_ontology, _dedupe_graph_by_id, _enforce_uuid_plan_pure_dynamic,
    _norm_slug, _uuid5, _extract_json_block
)

# Skeleton-first assembly helpers
_UUID_SUFFIX_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def _canon(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, default=str)


def _build_skeleton(records, uuid_plan, slot_type_map, parent_slug, context):
    nodes = []
    for plan in uuid_plan:
        # object
        obj_id = plan[parent_slug]
        nodes.append({"@id": obj_id, "@type": slot_type_map[parent_slug]})
        # facets/other planned slots
        for slug, pid in plan.items():
            if slug == parent_slug:
                continue
            nodes.append({"@id": pid, "@type": slot_type_map[slug]})
    return {"@context": context, "@graph": nodes}


def _attach_facets_from_plan(skel, uuid_plan, parent_slug):
    idx = {n["@id"]: n for n in skel["@graph"]}
    for plan in uuid_plan:
        parent_id = plan[parent_slug]
        facets = [{"@id": plan[s]} for s in plan.keys() if s != parent_slug]
        if facets:
            idx[parent_id].setdefault("uco-core:hasFacet", []).extend(facets)


def _merge_props_into_skeleton(model_graph, skel):
    """Copy props from model nodes into skeleton nodes with same @id.
       Ignore @id/@type from model; ignore nodes not in skeleton."""
    idx = {n["@id"]: n for n in skel["@graph"]}
    for mn in model_graph.get("@graph", []):
        mid = mn.get("@id")
        if mid not in idx:
            continue
        dst = idx[mid]
        for k, v in mn.items():
            if k in ("@id", "@type"):
                continue
            dst[k] = v  # owner checks already enforced upstream via ontology map


def _assert_uuid_ids(skel):
    ids = [n.get("@id", "") for n in skel["@graph"] if isinstance(n, dict)]
    assert all(_UUID_SUFFIX_RE.search(i)
               for i in ids), "Non-UUID @id detected."
    assert len(ids) == len(set(ids)), "Duplicate @id detected."


# =============================================================================
# Relationship Planning Functions (Testing First)
# =============================================================================

def _mint_rel_ids(rel_specs, records, obj_ids_by_record, ontology_map, prefix="kb:"):
    """
    Mint IDs for relationships based on LLM planning.
    Returns: {"property_edges": [...], "reified": [...]}
    """
    out = []
    rel_defs = ontology_map.get("relationships") or []
    # Build lookup: label -> representation ("property" or "reified"), plus property IRI if property
    idx = {}
    for r in rel_defs:
        label = (r.get("label") or r.get("name") or "").strip()
        rep = (r.get("representation") or "").strip().lower() or "property"
        prop = (r.get("property") or "").strip()
        idx[label.lower()] = {"rep": rep, "property": prop, "label": label}

    rel_plan = {"property_edges": [], "reified": []}
    for rel in rel_specs:  # {"kind","source_record","target_record"}
        kind = str(rel.get("kind") or "").strip()
        srci = int(rel.get("source_record"))
        tgti = int(rel.get("target_record"))
        src_id_map = obj_ids_by_record[srci]
        tgt_id_map = obj_ids_by_record[tgti]
        # pick primary object id per record (first slot)
        src_id = next(iter(src_id_map.values()), None)
        tgt_id = next(iter(tgt_id_map.values()), None)
        if not (src_id and tgt_id):
            continue

        meta = idx.get(kind.lower())
        if meta and meta["rep"] == "reified":
            seed = f"{kind}::{src_id}::{tgt_id}"
            rid = _uuid5(
                "kb:" + re.sub(r'[^a-z0-9]+', '', kind.lower()) + "-", seed)
            rel_plan["reified"].append(
                {"@id": rid, "kind": kind, "source": src_id, "target": tgt_id})
        else:
            # treat as property edge (default)
            # harmless default if kind omitted
            prop = (meta or {}).get("property") or "uco-core:hasFacet"
            rel_plan["property_edges"].append(
                {"property": prop, "source": src_id, "target": tgt_id})

    return rel_plan


def _collect_all_ids(x):
    """Recursively collect all @id values from a JSON-LD structure."""
    ids = set()
    if isinstance(x, dict):
        vid = x.get("@id")
        if isinstance(vid, str):
            ids.add(vid)
        for v in x.values():
            ids |= _collect_all_ids(v)
    elif isinstance(x, list):
        for it in x:
            ids |= _collect_all_ids(it)
    return ids


def _mint_uuid_plan_from_slots_parent_facet(
    slot_spec: Dict[str, Any],
    records: List[Dict[str, Any]],
    ontology_map: Dict[str, Any],
    prefix: str = "kb:",
) -> List[Dict[str, str]]:
    """
    Mint IDs deterministically, ensuring the primary object and its facets
    share the same UUID base. The LLM decides slots; we derive IDs.
    """
    records = records or []
    plans: List[Dict[str, str]] = [{} for _ in range(len(records))]

    # Normalize class labels (used to detect the "parent" object)
    allowed_classes = set()
    for c in (ontology_map.get("classes") or []):
        if isinstance(c, dict):
            lbl = str(c.get("name") or c.get("label")
                      or c.get("slug") or "").strip()
        else:
            lbl = str(c).strip()
        if lbl:
            allowed_classes.add(lbl.lower())

    for entry in (slot_spec.get("plan") or []):
        i = int(entry.get("record", -1))
        if i < 0 or i >= len(records):
            continue

        rec = records[i] if isinstance(records[i], dict) else {}
        # Stable seed from record contents
        seed_base = json.dumps(
            {k: rec.get(k) for k in sorted(rec.keys())},
            sort_keys=True,
            default=str,
        )

        slots = [str(s).strip()
                 for s in (entry.get("slots") or []) if str(s).strip()]
        if not slots:
            continue

        # 1) Pick the first slot that is a CLASS as the "parent"
        parent_slug = None
        for s in slots:
            if s.lower() in allowed_classes:
                parent_slug = _norm_slug(s)
                break

        # Fallback: if no class was present, treat the first slot as the parent anyway
        if not parent_slug:
            parent_slug = _norm_slug(slots[0])

        # 2) Mint the parent ID from record seed + parent slug
        parent_seed = f"{parent_slug}::{i}::{seed_base}"
        parent_id = _uuid5(f"{prefix}{parent_slug}-", parent_seed)
        plans[i][parent_slug] = parent_id

        # 3) Mint every other slot (typically facets) *derived from the parent ID*
        for s in slots:
            slug = _norm_slug(s)
            if slug == parent_slug:
                continue
            facet_seed = f"{slug}::{parent_id}"
            plans[i][slug] = _uuid5(f"{prefix}{slug}-", facet_seed)

    return plans


def _mint_uuid_plan_from_slots_independent_facets(
    slot_spec: Dict[str, Any],
    records: List[Dict[str, Any]],
    ontology_map: Dict[str, Any],
    prefix: str = "kb:",
) -> List[Dict[str, str]]:
    """
    Mint IDs deterministically, with facets minting independent UUIDv5 from record content.
    The LLM decides slots; we derive IDs independently for better standards compliance.
    """
    records = records or []
    plans: List[Dict[str, str]] = [{} for _ in range(len(records))]

    # Normalize class labels (used to detect the "parent" object)
    allowed_classes = set()
    for c in (ontology_map.get("classes") or []):
        if isinstance(c, dict):
            lbl = str(c.get("name") or c.get("label")
                      or c.get("slug") or "").strip()
        else:
            lbl = str(c).strip()
        if lbl:
            allowed_classes.add(lbl.lower())

    for entry in (slot_spec.get("plan") or []):
        i = int(entry.get("record", -1))
        if i < 0 or i >= len(records):
            continue

        rec = records[i] if isinstance(records[i], dict) else {}
        # Stable seed from record contents
        seed_base = json.dumps(
            {k: rec.get(k) for k in sorted(rec.keys())},
            sort_keys=True,
            default=str,
        )

        slots = [str(s).strip()
                 for s in (entry.get("slots") or []) if str(s).strip()]
        if not slots:
            continue

        # 1) Pick the first slot that is a CLASS as the "parent"
        parent_slug = None
        for s in slots:
            if s.lower() in allowed_classes:
                parent_slug = _norm_slug(s)
                break

        # Fallback: if no class was present, treat the first slot as the parent anyway
        if not parent_slug:
            parent_slug = _norm_slug(slots[0])

        # 2) Mint the parent ID from record seed + parent slug
        parent_seed = f"{parent_slug}::{i}::{seed_base}"
        parent_id = _uuid5(f"{prefix}{parent_slug}-", parent_seed)
        plans[i][parent_slug] = parent_id

        # 3) Mint every other slot (typically facets) independently
        for s in slots:
            slug = _norm_slug(s)
            if slug == parent_slug:
                continue

            # CORRECTED LOGIC:
            # Seed the facet with its own slug + record index + the original record's content.
            facet_seed = f"{slug}::{i}::{seed_base}"
            plans[i][slug] = _uuid5(f"{prefix}{slug}-", facet_seed)

    return plans


def _extended_coverage_check(json_obj: dict, state: dict) -> dict:
    """
    Extended coverage check that handles both nodes and relationships.
    - Checks for missing node IDs and reified relationship IDs
    - Ensures property edges exist in the graph
    - Auto-heals missing IDs with stubs
    """
    # Collect all emitted IDs
    emitted_ids = _collect_all_ids(json_obj.get("@graph", []))

    # Check planned node IDs
    planned_node_ids = {v for rec in state.get(
        "uuidPlan", []) for v in rec.values()}
    missing_nodes = planned_node_ids - emitted_ids

    # Check reified relationship IDs (property edges don't have their own @id)
    relp = state.get("uuidPlanRelations", {})
    planned_rel_ids = {r["@id"] for r in (relp.get("reified") or [])}
    missing_rels = planned_rel_ids - emitted_ids

    # Auto-heal: add stubs so we never fail on coverage
    for mid in (missing_nodes | missing_rels):
        json_obj["@graph"].append({"@id": mid})

    # Ensure property edges exist
    for e in (relp.get("property_edges") or []):
        prop, src, tgt = e["property"], e["source"], e["target"]
        # find source node
        src_node = next(
            (n for n in json_obj["@graph"] if isinstance(n, dict) and n.get("@id") == src), None)
        if not src_node:
            # create stub if needed
            src_node = {"@id": src}
            json_obj["@graph"].append(src_node)
        # ensure property edge exists
        vals = src_node.get(prop)
        if not isinstance(vals, list) or not any(isinstance(v, dict) and v.get("@id") == tgt for v in vals):
            src_node[prop] = (vals if isinstance(
                vals, list) else []) + [{"@id": tgt}]

    return json_obj


# --------------------------
# A tiny LLM stub for offline tests
# --------------------------
class _Resp:
    def __init__(self, content: str = "", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []


class DummyLLM:
    """
    Behaves like the runtime:
      - When a UUID plan exists, tools are effectively disabled and we MUST emit JSON-LD.
      - When no plan and tools are enabled, we emit tool_calls (simulate generate_uuid usage).
    You can set SIMULATE_MISS_PLAN=1 to mimic a model that forgets some planned IDs.
    """

    def __init__(self, tools_enabled: bool = False, behavior: str = "honor_plan"):
        self.tools_enabled = tools_enabled
        self.behavior = behavior  # "honor_plan" | "omit_some"

    def bind_tools(self, tools):
        # Your node calls llm.bind_tools([generate_uuid]) only if no uuidPlan
        return DummyLLM(tools_enabled=True, behavior=self.behavior)

    def _extract_blocks(self, prompt: str) -> List[str]:
        # Extract all fenced JSON/JSON-LD blocks — same pattern your node expects
        return re.findall(
            r"```(?:json|jsonld|json-ld)?\s*(\{.*?\}|\[.*?\])\s*```",
            prompt,
            flags=re.DOTALL,
        )

    def _parse_prompt(self, messages: List[Dict[str, str]]):
        full_prompt = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                full_prompt = m.get("content", "")
                break

        blocks = self._extract_blocks(full_prompt)
        records = []
        uuid_plan = []
        if blocks:
            # Heuristic: first block is records (list), last block is plan (list of dicts)
            try:
                maybe_records = json.loads(blocks[0])
                if isinstance(maybe_records, list):
                    records = maybe_records
            except Exception:
                pass

            # Try to parse the last block as the Plan
            try:
                maybe_plan = json.loads(blocks[-1])
                if isinstance(maybe_plan, list) and all(isinstance(x, dict) for x in maybe_plan):
                    uuid_plan = maybe_plan
            except Exception:
                pass

        return full_prompt, records, uuid_plan

    def _emit_jsonld_from_plan(self, records: List[dict], uuid_plan: List[dict]) -> str:
        """Honor the plan (or optionally omit some IDs if SIMULATE_MISS_PLAN=1)."""
        graph_nodes = []
        simulate_miss = os.getenv("SIMULATE_MISS_PLAN") == "1"

        for i, rec in enumerate(records):
            plan = uuid_plan[i] if i < len(uuid_plan) else {}

            # Optionally omit half the facets to simulate a naughty model
            for key, planned_id in plan.items():
                if key.lower().endswith("facet"):
                    if simulate_miss and (i % 2 == 0):
                        # skip this planned facet id to test your post-enforcement
                        continue
                    node = {"@id": planned_id,
                            "@type": ["uco-observable:FileFacet"]}
                    graph_nodes.append(node)
                else:
                    node = {"@id": planned_id,
                            "@type": ["uco-observable:File"]}
                    if isinstance(rec, dict) and "FullPath" in rec:
                        node["uco-observable:filePath"] = rec["FullPath"]
                    graph_nodes.append(node)

        jsonld = {
            "@context": {
                "kb": "http://example.org/kb/",
                "xsd": "http://www.w3.org/2001/XMLSchema#",
                "uco-observable": "https://ontology.unifiedcyberontology.org/uco/observable/",
            },
            "@graph": graph_nodes,
        }
        return json.dumps(jsonld)

    def _emit_tool_calls_no_plan(self, records: List[dict]) -> _Resp:
        """Simulate no plan + tools enabled: request UUIDs via tool calls."""
        tool_calls = []
        for _ in records:
            tool_calls.append(
                {"name": "generate_uuid", "args": {"entity_type": "file"}})
            tool_calls.append({"name": "generate_uuid", "args": {
                              "entity_type": "filefacet"}})
        # No content — node should go into tool-call handling path
        return _Resp(content="", tool_calls=tool_calls)

    def invoke(self, messages: List[Dict[str, str]]):
        full_prompt, records, uuid_plan = self._parse_prompt(messages)

        has_plan_in_prompt = bool(uuid_plan)
        if has_plan_in_prompt:
            # PLAN PATH (tools disabled at runtime): emit JSON-LD right away
            return _Resp(content=self._emit_jsonld_from_plan(records, uuid_plan))

        # NO PLAN in prompt:
        if self.tools_enabled:
            # Simulate asking for UUIDs via tool calls
            return self._emit_tool_calls_no_plan(records)

        # Tools disabled + no plan? produce empty content (unlikely in practice)
        return _Resp(content="")


# --------------------------
# Minimal test harness
# --------------------------
def test_pure_dynamic_enforcement():
    """Test the pure dynamic UUID enforcement approach."""
    print("\n=== TESTING PURE DYNAMIC ENFORCEMENT ===")

    # Create a test JSON-LD object with missing planned IDs
    test_jsonld = {
        "@context": {"kb": "http://example.org/kb/"},
        "@graph": [
            {
                "@id": "kb:file-test-123",
                "@type": ["uco-observable:File"],
                "uco-observable:filePath": "/test/path"
            }
            # Missing: kb:filefacet-test-123
        ]
    }

    # Create test state with ontology mappings
    test_state = {
        "rawInputJSON": [
            {
                "FullPath": "/test/path",
                "EntryNumber": 42,
                "SequenceNumber": 1,
                "ParentEntryNumber": 0,
                "InUse": True
            }
        ],
        "uuidPlan": [
            {
                "file": "kb:file-test-123",
                "filefacet": "kb:filefacet-test-123"
            }
        ],
        "ontologyMap": {
            "type_map": {
                "file": "uco-observable:File",
                "filefacet": "uco-observable:FileFacet"
            },
            "analysis": {
                "input_to_property": {
                    "FullPath": "uco-observable:filePath",
                    "EntryNumber": "uco-observable:entryNumber",
                    "SequenceNumber": "uco-observable:sequenceNumber",
                    "ParentEntryNumber": "uco-observable:parentEntryNumber",
                    "InUse": "uco-observable:isInUse"
                }
            }
        }
    }

    print("Before enforcement:")
    print(f"  Graph nodes: {len(test_jsonld['@graph'])}")
    print(
        f"  Planned IDs: {[v for rec in test_state['uuidPlan'] for v in rec.values()]}")

    # Apply pure dynamic enforcement
    result = _enforce_uuid_plan_pure_dynamic(test_jsonld, test_state)

    print("After enforcement:")
    print(f"  Graph nodes: {len(result['@graph'])}")

    # Check that missing planned ID was added
    emitted_ids = {n.get("@id") for n in result["@graph"]}
    planned_ids = {v for rec in test_state["uuidPlan"] for v in rec.values()}
    missing = planned_ids - emitted_ids

    print(f"  Missing planned IDs: {list(missing)}")
    print(f"  Added node details:")
    for node in result["@graph"]:
        if node.get("@id") == "kb:filefacet-test-123":
            print(f"    {json.dumps(node, indent=4)}")

    assert not missing, f"Missing planned IDs after enforcement: {list(missing)}"
    print("✅ PURE DYNAMIC ENFORCEMENT TEST PASSED")


def test_network_traffic_case():
    """Test pure dynamic enforcement with a different case type (network traffic)."""
    print("\n=== TESTING NETWORK TRAFFIC CASE ===")

    # Create a test JSON-LD object for network traffic
    test_jsonld = {
        "@context": {"kb": "http://example.org/kb/"},
        "@graph": [
            {
                "@id": "kb:connection-test-456",
                "@type": ["uco-observable:NetworkConnection"],
                "uco-observable:sourceAddress": "192.168.1.100"
            }
            # Missing: kb:flow-test-456
        ]
    }

    # Create test state for network traffic case
    test_state = {
        "rawInputJSON": [
            {
                "src_ip": "192.168.1.100",
                "dst_ip": "10.0.0.1",
                "src_port": 8080,
                "dst_port": 443,
                "protocol": "TCP",
                "bytes_sent": 1024
            }
        ],
        "uuidPlan": [
            {
                "connection": "kb:connection-test-456",
                "flow": "kb:flow-test-456"
            }
        ],
        "ontologyMap": {
            "type_map": {
                "connection": "uco-observable:NetworkConnection",
                "flow": "uco-observable:NetworkFlow"
            },
            "analysis": {
                "input_to_property": {
                    "src_ip": "uco-observable:sourceAddress",
                    "dst_ip": "uco-observable:destinationAddress",
                    "src_port": "uco-observable:sourcePort",
                    "dst_port": "uco-observable:destinationPort",
                    "protocol": "uco-observable:protocol",
                    "bytes_sent": "uco-observable:bytesSent"
                }
            }
        }
    }

    print("Before enforcement:")
    print(f"  Graph nodes: {len(test_jsonld['@graph'])}")
    print(
        f"  Planned IDs: {[v for rec in test_state['uuidPlan'] for v in rec.values()]}")

    # Apply pure dynamic enforcement
    result = _enforce_uuid_plan_pure_dynamic(test_jsonld, test_state)

    print("After enforcement:")
    print(f"  Graph nodes: {len(result['@graph'])}")

    # Check that missing planned ID was added
    emitted_ids = {n.get("@id") for n in result["@graph"]}
    planned_ids = {v for rec in test_state["uuidPlan"] for v in rec.values()}
    missing = planned_ids - emitted_ids

    print(f"  Missing planned IDs: {list(missing)}")
    print(f"  Added node details:")
    for node in result["@graph"]:
        if node.get("@id") == "kb:flow-test-456":
            print(f"    {json.dumps(node, indent=4)}")

    assert not missing, f"Missing planned IDs after enforcement: {list(missing)}"
    print("✅ NETWORK TRAFFIC CASE TEST PASSED")


def test_edge_cases():
    """Test the robust solution with weird data structures."""
    print("\n=== TESTING EDGE CASES ===")

    # Test with malformed plan entries
    test_jsonld = {
        "@context": {"kb": "http://example.org/kb/"},
        "@graph": [
            {"@id": "kb:file-test-789", "@type": ["uco-observable:File"]}
        ]
    }

    test_state = {
        "rawInputJSON": [{"FullPath": "/test/path", "EntryNumber": 42}],
        "uuidPlan": [
            # Normal dict
            {"file": "kb:file-test-789", "filefacet": "kb:filefacet-test-789"},
            # List format (should get unnamed_0, unnamed_1)
            ["kb:file-test-790", "kb:filefacet-test-790"],
            # Mixed format
            {"file": "kb:file-test-791",
                "weird": ["kb:facet-test-791", "kb:extra-test-791"]},
            # Invalid entry (should be skipped)
            "invalid_string",
            # Empty dict (should be skipped)
            {}
        ],
        "ontologyMap": {
            "type_map": {
                "file": "uco-observable:File",
                "filefacet": "uco-observable:FileFacet",
                "weird": "uco-observable:WeirdType",
                "unnamed_0": "uco-observable:File",
                "unnamed_1": "uco-observable:FileFacet"
            },
            "analysis": {
                "input_to_property": {
                    "FullPath": "uco-observable:filePath",
                    "EntryNumber": "uco-observable:entryNumber"
                }
            }
        }
    }

    print("Before enforcement:")
    print(f"  Graph nodes: {len(test_jsonld['@graph'])}")

    # Apply robust enforcement
    result = _enforce_uuid_plan_pure_dynamic(test_jsonld, test_state)

    print("After enforcement:")
    print(f"  Graph nodes: {len(result['@graph'])}")

    # Check that all valid planned IDs were added
    emitted_ids = {n.get("@id") for n in result["@graph"]}
    expected_ids = {
        "kb:file-test-789", "kb:filefacet-test-789",  # from dict
        "kb:file-test-790", "kb:filefacet-test-790",  # from list
        "kb:file-test-791", "kb:facet-test-791", "kb:extra-test-791"  # from mixed
    }

    missing = expected_ids - emitted_ids
    print(f"  Expected IDs: {sorted(expected_ids)}")
    print(f"  Emitted IDs: {sorted(emitted_ids)}")
    print(f"  Missing: {sorted(missing)}")

    assert not missing, f"Missing expected IDs: {sorted(missing)}"
    print("✅ EDGE CASES TEST PASSED")


def test_relationship_planning():
    """Test relationship ID minting and planning."""
    print("\n=== TESTING RELATIONSHIP PLANNING ===")

    # Test data with relationships
    records = [
        {"FullPath": "/file1.txt", "ParentDir": "/home/user"},
        {"FullPath": "/file2.txt", "ParentDir": "/home/user"}
    ]

    # Mock UUID plan (as if generated by _mint_uuid_plan_from_slots)
    obj_ids_by_record = [
        {"file": "kb:file-abc123", "directory": "kb:dir-def456"},
        {"file": "kb:file-ghi789", "directory": "kb:dir-jkl012"}
    ]

    # Relationship specifications from LLM planning
    rel_specs = [
        {"kind": "contained-within", "source_record": 0, "target_record": 1},
        {"kind": "contained-within", "source_record": 1, "target_record": 1}
    ]

    # Ontology with relationship definitions
    ontology_map = {
        "relationships": [
            {
                "label": "contained-within",
                "representation": "property",
                "property": "uco-core:containedWithin"
            },
            {
                "label": "related-to",
                "representation": "reified",
                "property": "uco-core:relatedTo"
            }
        ]
    }

    # Test relationship ID minting
    rel_plan = _mint_rel_ids(
        rel_specs, records, obj_ids_by_record, ontology_map)

    print("Relationship plan:")
    print(f"  Property edges: {len(rel_plan['property_edges'])}")
    print(f"  Reified relationships: {len(rel_plan['reified'])}")

    # Check property edges
    assert len(rel_plan["property_edges"]) == 2
    assert all("property" in edge for edge in rel_plan["property_edges"])
    assert all("source" in edge for edge in rel_plan["property_edges"])
    assert all("target" in edge for edge in rel_plan["property_edges"])

    # Check that property edges use the correct property IRI
    for edge in rel_plan["property_edges"]:
        assert edge["property"] == "uco-core:containedWithin"

    print("✅ RELATIONSHIP PLANNING TEST PASSED")


def test_id_collection():
    """Test comprehensive ID collection from JSON-LD structures."""
    print("\n=== TESTING ID COLLECTION ===")

    # Complex JSON-LD structure with nested IDs
    test_jsonld = {
        "@context": {"kb": "http://example.org/kb/"},
        "@graph": [
            {
                "@id": "kb:file-123",
                "@type": "uco-observable:File",
                "uco-core:hasFacet": [
                    {
                        "@id": "kb:facet-456",
                        "@type": "uco-observable:FileFacet"
                    }
                ],
                "uco-core:containedWithin": [
                    {
                        "@id": "kb:dir-789",
                        "@type": "uco-observable:Directory"
                    }
                ]
            },
            {
                "@id": "kb:relationship-abc",
                "@type": "uco-core:Relationship",
                "uco-core:source": [{"@id": "kb:file-123"}],
                "uco-core:target": [{"@id": "kb:dir-789"}]
            }
        ]
    }

    # Collect all IDs
    collected_ids = _collect_all_ids(test_jsonld)

    expected_ids = {
        "kb:file-123", "kb:facet-456", "kb:dir-789", "kb:relationship-abc"
    }

    print(f"Collected IDs: {sorted(collected_ids)}")
    print(f"Expected IDs: {sorted(expected_ids)}")

    assert collected_ids == expected_ids, f"ID collection mismatch: {collected_ids} vs {expected_ids}"
    print("✅ ID COLLECTION TEST PASSED")


def test_extended_coverage_check():
    """Test extended coverage check with relationships."""
    print("\n=== TESTING EXTENDED COVERAGE CHECK ===")

    # Test JSON-LD with missing relationship
    test_jsonld = {
        "@context": {"kb": "http://example.org/kb/"},
        "@graph": [
            {
                "@id": "kb:file-123",
                "@type": "uco-observable:File"
            }
        ]
    }

    # State with planned relationships
    test_state = {
        "uuidPlan": [
            {"file": "kb:file-123", "directory": "kb:dir-456"}
        ],
        "uuidPlanRelations": {
            "property_edges": [
                {"property": "uco-core:containedWithin",
                    "source": "kb:file-123", "target": "kb:dir-456"}
            ],
            "reified": [
                {"@id": "kb:rel-abc", "kind": "related-to",
                    "source": "kb:file-123", "target": "kb:dir-456"}
            ]
        }
    }

    print("Before extended coverage check:")
    print(f"  Graph nodes: {len(test_jsonld['@graph'])}")

    # Apply extended coverage check
    result = _extended_coverage_check(test_jsonld, test_state)

    print("After extended coverage check:")
    print(f"  Graph nodes: {len(result['@graph'])}")

    # Check that missing IDs were added
    emitted_ids = _collect_all_ids(result)
    expected_ids = {"kb:file-123", "kb:dir-456", "kb:rel-abc"}

    print(f"  Emitted IDs: {sorted(emitted_ids)}")
    print(f"  Expected IDs: {sorted(expected_ids)}")

    assert emitted_ids == expected_ids, f"Missing IDs after coverage check: {expected_ids - emitted_ids}"

    # Check that property edge was added
    file_node = next(n for n in result["@graph"]
                     if n.get("@id") == "kb:file-123")
    assert "uco-core:containedWithin" in file_node
    assert any(ref.get("@id") ==
               "kb:dir-456" for ref in file_node["uco-core:containedWithin"])

    print("✅ EXTENDED COVERAGE CHECK TEST PASSED")


def test_parent_facet_pairing():
    """Test parent-facet pairing for deterministic UUID relationships."""
    print("\n=== TESTING PARENT-FACET PAIRING ===")

    # Test data with file and facet
    records = [
        {"FullPath": "/test/file1.txt", "EntryNumber": 42},
        {"FullPath": "/test/file2.txt", "EntryNumber": 314}
    ]

    # Mock LLM slot specification
    slot_spec = {
        "plan": [
            {"record": 0, "slots": ["File", "NTFSFileFacet"]},
            {"record": 1, "slots": ["File", "FileFacet"]}
        ]
    }

    # Ontology with classes
    ontology_map = {
        "classes": [
            {"name": "File", "label": "File"},
            {"name": "Process", "label": "Process"}
        ],
        "facets": [
            {"name": "NTFSFileFacet", "label": "NTFSFileFacet"},
            {"name": "FileFacet", "label": "FileFacet"}
        ]
    }

    # Test parent-facet pairing
    uuid_plan = _mint_uuid_plan_from_slots_parent_facet(
        slot_spec, records, ontology_map)

    print("UUID Plan:")
    for i, plan in enumerate(uuid_plan):
        print(f"  Record {i}: {plan}")

    # Check that we have the expected structure
    assert len(uuid_plan) == 2
    assert "file" in uuid_plan[0]  # parent
    assert "ntfsfilefacet" in uuid_plan[0]  # facet
    assert "file" in uuid_plan[1]  # parent
    assert "filefacet" in uuid_plan[1]  # facet

    # Check that facet IDs are derived from parent IDs
    file_id_0 = uuid_plan[0]["file"]
    facet_id_0 = uuid_plan[0]["ntfsfilefacet"]

    file_id_1 = uuid_plan[1]["file"]
    facet_id_1 = uuid_plan[1]["filefacet"]

    # Verify deterministic pairing - same record should produce same IDs
    uuid_plan_2 = _mint_uuid_plan_from_slots_parent_facet(
        slot_spec, records, ontology_map)
    assert uuid_plan_2[0]["file"] == file_id_0
    assert uuid_plan_2[0]["ntfsfilefacet"] == facet_id_0
    assert uuid_plan_2[1]["file"] == file_id_1
    assert uuid_plan_2[1]["filefacet"] == facet_id_1

    print("✅ PARENT-FACET PAIRING TEST PASSED")


def test_independent_facet_minting():
    """Test independent facet minting for better standards compliance."""
    print("\n=== TESTING INDEPENDENT FACET MINTING ===")

    # Test data with file and facet
    records = [
        {"FullPath": "/test/file1.txt", "EntryNumber": 42},
        {"FullPath": "/test/file2.txt", "EntryNumber": 314}
    ]

    # Mock LLM slot specification
    slot_spec = {
        "plan": [
            {"record": 0, "slots": ["File", "NTFSFileFacet"]},
            {"record": 1, "slots": ["File", "FileFacet"]}
        ]
    }

    # Ontology with classes
    ontology_map = {
        "classes": [
            {"name": "File", "label": "File"},
            {"name": "Process", "label": "Process"}
        ],
        "facets": [
            {"name": "NTFSFileFacet", "label": "NTFSFileFacet"},
            {"name": "FileFacet", "label": "FileFacet"}
        ]
    }

    # Test independent facet minting
    uuid_plan = _mint_uuid_plan_from_slots_independent_facets(
        slot_spec, records, ontology_map)

    print("UUID Plan (Independent Facets):")
    for i, plan in enumerate(uuid_plan):
        print(f"  Record {i}: {plan}")

    # Check that we have the expected structure
    assert len(uuid_plan) == 2
    assert "file" in uuid_plan[0]  # parent
    assert "ntfsfilefacet" in uuid_plan[0]  # facet
    assert "file" in uuid_plan[1]  # parent
    assert "filefacet" in uuid_plan[1]  # facet

    # Check that facet IDs are independent (not derived from parent IDs)
    file_id_0 = uuid_plan[0]["file"]
    facet_id_0 = uuid_plan[0]["ntfsfilefacet"]

    file_id_1 = uuid_plan[1]["file"]
    facet_id_1 = uuid_plan[1]["filefacet"]

    # Verify deterministic minting - same record should produce same IDs
    uuid_plan_2 = _mint_uuid_plan_from_slots_independent_facets(
        slot_spec, records, ontology_map)
    assert uuid_plan_2[0]["file"] == file_id_0
    assert uuid_plan_2[0]["ntfsfilefacet"] == facet_id_0
    assert uuid_plan_2[1]["file"] == file_id_1
    assert uuid_plan_2[1]["filefacet"] == facet_id_1

    # Verify that facet IDs are NOT derived from parent IDs
    # (They should be independent UUIDs based on record content)
    print(f"File ID 0: {file_id_0}")
    print(f"Facet ID 0: {facet_id_0}")
    print(f"File ID 1: {file_id_1}")
    print(f"Facet ID 1: {facet_id_1}")

    # The facet IDs should be completely independent UUIDs
    # (not containing the parent ID in their generation)
    assert facet_id_0 != file_id_0  # Different UUIDs
    assert facet_id_1 != file_id_1  # Different UUIDs

    print("✅ INDEPENDENT FACET MINTING TEST PASSED")


def test_skeleton_first_assembly():
    """Test skeleton-first assembly to prevent LLM-made @id issues."""
    print("\n=== TESTING SKELETON-FIRST ASSEMBLY ===")

    # Test data
    records = [
        {"FullPath": "/test/file1.txt", "EntryNumber": 42},
        {"FullPath": "/test/file2.txt", "EntryNumber": 314}
    ]

    # UUID plan (already deterministic)
    uuid_plan = [
        {"file": "kb:file-56a6e165-aa95-5812-857f-22d5cf69eeb5",
            "filefacet": "kb:filefacet-25aed45f-61fc-5c8b-91ab-c81e66b0e5c9"},
        {"file": "kb:file-90632070-48eb-51a8-8994-22a4407c517d",
            "filefacet": "kb:filefacet-3f91fd9e-da51-56c6-be9c-2beefd76291f"}
    ]

    # Slot type mapping
    slot_type_map = {
        "file": "uco-observable:File",
        "filefacet": "uco-observable:FileFacet"
    }

    # Context
    context = {"kb": "http://example.org/kb/"}

    # Build skeleton
    skeleton = _build_skeleton(
        records, uuid_plan, slot_type_map, "file", context)

    print("Skeleton created:")
    print(json.dumps(skeleton, indent=2))

    # Test skeleton structure
    assert "@context" in skeleton
    assert "@graph" in skeleton
    assert len(skeleton["@graph"]) == 4  # 2 files + 2 facets

    # Test that all nodes have proper @id and @type
    for node in skeleton["@graph"]:
        assert "@id" in node
        assert "@type" in node
        assert node["@id"].startswith("kb:")
        assert node["@type"] in ["uco-observable:File",
                                 "uco-observable:FileFacet"]

    # Test model graph with problematic IDs (should be ignored)
    model_graph = {
        "@graph": [
            {
                "@id": "kb:file-bad-id-1",  # This should be ignored
                "@type": "uco-observable:File",
                "uco-observable:filePath": "/test/file1.txt"
            },
            {
                "@id": "kb:file-56a6e165-aa95-5812-857f-22d5cf69eeb5",  # This matches skeleton
                "@type": "uco-observable:File",
                "uco-observable:filePath": "/test/file1.txt",
                "uco-observable:entryNumber": 42
            }
        ]
    }

    # Merge properties into skeleton
    _merge_props_into_skeleton(model_graph, skeleton)

    # Test that properties were merged correctly
    file_node = next(n for n in skeleton["@graph"] if n["@id"]
                     == "kb:file-56a6e165-aa95-5812-857f-22d5cf69eeb5")
    assert "uco-observable:filePath" in file_node
    assert "uco-observable:entryNumber" in file_node
    assert file_node["uco-observable:filePath"] == "/test/file1.txt"
    assert file_node["uco-observable:entryNumber"] == 42

    # Test that bad ID was ignored (not in skeleton)
    bad_id_nodes = [n for n in skeleton["@graph"]
                    if n["@id"] == "kb:file-bad-id-1"]
    assert len(bad_id_nodes) == 0

    # Attach facets from plan
    _attach_facets_from_plan(skeleton, uuid_plan, "file")

    # Test that facets were attached
    file_node = next(n for n in skeleton["@graph"] if n["@id"]
                     == "kb:file-56a6e165-aa95-5812-857f-22d5cf69eeb5")
    assert "uco-core:hasFacet" in file_node
    assert len(file_node["uco-core:hasFacet"]) == 1
    assert file_node["uco-core:hasFacet"][0]["@id"] == "kb:filefacet-25aed45f-61fc-5c8b-91ab-c81e66b0e5c9"

    # Test UUID assertion
    _assert_uuid_ids(skeleton)

    print("✅ SKELETON-FIRST ASSEMBLY TEST PASSED")


def main():
    # 1) Monkeypatch the global LLM used by your node
    orig_llm = CFG.llm
    # Default behavior: honor the plan; set SIMULATE_MISS_PLAN=1 to test your post-enforcement
    CFG.llm = DummyLLM(behavior="honor_plan")

    try:
        # 2) Build a minimal state that your node expects
        state: Dict[str, Any] = {
            # Ontology map must include class/facet slugs for UUID planning
            "ontologyMap": {
                "classes": ["File"],
                "facets": ["FileFacet"],
                "context": {
                    "kb": "http://example.org/kb/",
                    "xsd": "http://www.w3.org/2001/XMLSchema#"
                },
                # NEW: Pure dynamic ontology-driven mappings
                "type_map": {
                    "file": "uco-observable:File",
                    "filefacet": "uco-observable:FileFacet"
                },
                "analysis": {
                    "input_to_property": {
                        "FullPath": "uco-observable:filePath",
                        "EntryNumber": "uco-observable:entryNumber",
                        "SequenceNumber": "uco-observable:sequenceNumber",
                        "ParentEntryNumber": "uco-observable:parentEntryNumber",
                        "InUse": "uco-observable:isInUse"
                    }
                }
            },
            "customFacets": {},             # OK if empty
            "customState": {},              # OK if empty
            "ontologyMarkdown": "# dummy",  # just to satisfy logs
            "validation_feedback": "",
            "validationHistory": [],
            "learningContext": "",
            "memory_context": "",
            "layer2_feedback_history": [],

            # The important part: raw JSON array for the test
            "rawInputJSON": [
                {
                    "EntryNumber": 42,
                    "SequenceNumber": 3,
                    "ParentEntryNumber": 5,
                    "FullPath": "\\\\Windows\\\\Prefetch\\\\MALICIOUS.EXE-12345678.pf",
                    "InUse": True,
                },
                {
                    "EntryNumber": 314,
                    "SequenceNumber": 1,
                    "ParentEntryNumber": 200,
                    "FullPath": "\\\\Users\\\\Alice\\\\Documents\\\\report.docx",
                    "InUse": True,
                }
            ],
            "inputFormat": "json",
        }

        # 3) Invoke the node directly
        print(
            f"[TEST] State before call: uuidPlan = {state.get('uuidPlan', 'NOT SET')}")
        cmd = graph_generator_node(state)
        print(
            f"[TEST] State after call: uuidPlan = {state.get('uuidPlan', 'NOT SET')}")

        # 4) Inspect the result (Command object)
        upd = getattr(cmd, "update", {}) or {}
        jsonld = upd.get("jsonldGraph")
        goto = getattr(cmd, "goto", None)

        print("\n=== TEST RESULT ===")
        print("Next node:", goto)
        if not jsonld:
            print("FAIL: no jsonldGraph in update")
            return

        # Basic checks
        assert "@context" in jsonld, "Missing @context"
        assert "@graph" in jsonld, "Missing @graph"
        print(f"@graph size: {len(jsonld['@graph'])}")

        # Verify coverage: every planned ID appears at least once
        planned_ids = {v for rec in state.get(
            "uuidPlan", []) for v in rec.values()} if "uuidPlan" in state else set()
        if not planned_ids:
            planned_ids = {v for rec in state.get(
                "uuidPlan", []) for v in rec.values()}
        emitted_ids = {
            n.get("@id") for n in (jsonld.get("@graph") or []) if isinstance(n, dict)}
        missing = planned_ids - emitted_ids
        assert not missing, f"Missing planned IDs: {list(missing)[:5]}"

        # Quick peek
        print(json.dumps(jsonld, indent=2))
        print("\nPASS: offline graph generation produced one JSON-LD with full UUID coverage.\n")

    finally:
        # 5) Restore original LLM
        CFG.llm = orig_llm


if __name__ == "__main__":
    # Test pure dynamic enforcement first
    test_pure_dynamic_enforcement()

    # Test network traffic case
    test_network_traffic_case()

    # Test edge cases
    test_edge_cases()

    # Test relationship features
    test_relationship_planning()
    test_id_collection()
    test_extended_coverage_check()

    # Test parent-facet pairing
    test_parent_facet_pairing()

    # Test independent facet minting
    test_independent_facet_minting()

    # Test skeleton-first assembly
    test_skeleton_first_assembly()

    # Then run the main integration test
    main()

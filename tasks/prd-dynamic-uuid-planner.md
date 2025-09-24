# Product Requirements Document: Dynamic UUID Planner

## 1. Introduction/Overview

This document outlines the requirements for a significant refactoring of the system's entity identification mechanism. The current planner, which uses non-deterministic `uuid4` identifiers, leads to data inconsistency, complicates debugging, and prevents the implementation of advanced features.

This feature, the **Dynamic UUID Planner**, will replace the existing implementation with a robust, deterministic, and incremental planning system. It will use content-based fingerprinting (SHA-256) and `uuid5` to generate stable and predictable IDs for all entities in the knowledge graph.

## 2. Goals

The primary goals of this feature are to:
-   Improve data consistency and reliability for analysts using the system.
-   Enable future features that depend on stable IDs, such as incremental updates and caching.
-   Reduce bugs, validation errors, and maintenance overhead caused by the current non-deterministic system.

## 3. User Stories

This feature addresses the needs of both developers and the end-users of the generated data:

-   **As a developer,** I want the system to generate stable and predictable IDs so that I can reliably debug, trace data across multiple runs, and build new features with confidence.
-   **As a data analyst,** I want the graph output to be consistent and deterministic so that I can trust the relationships and entities presented, and perform reliable longitudinal analysis.

## 4. Functional Requirements

The system shall be updated to meet the following functional requirements:

1.  **State Expansion:** The application `State` must be extended to include fields for managing the UUID plan, including `uuidPlan`, `slotTypeMap`, `recordFingerprints`, and `plannerVersion`.
2.  **Deterministic ID Generation:** The UUID planner must use the `uuid5` algorithm with a consistent namespace to generate all entity and record identifiers.
3.  **Content-Based Fingerprinting:** The planner must generate a SHA-256 fingerprint for each input record to uniquely identify it based on its content. Record and slot UUIDs will be derived from this fingerprint.
4.  **Incremental Planning:** The planner must support incremental updates. When input changes, it should only re-plan the rows for new, changed, or removed records, leaving the rest of the plan untouched.
5.  **Ontology-Driven Slot Derivation:** The planner must derive entity "slots" (e.g., `file`, `filefacet`) directly from the `ontologyMap` and `customFacets` for any given record. It should not use hardcoded string manipulation. Facet slots should only be included if the record contains properties owned by that facet.
6.  **Relationship Planning:** The planner must automatically add slots for `uco-observable:ObservableRelationship` nodes when relationships are defined in the `ontologyMap` for a record.
7.  **Type Mapping:** The planner must produce a `slotTypeMap` that maps every generated `@id` to its full IRI `@type` (e.g., `https://ontology.unifiedcyberontology.org/uco/observable/FileFacet`).
8.  **Generator Alignment:** The `graph_generator_node` must be updated to consume the `uuidPlan` and `slotTypeMap` to construct the graph skeleton, setting the `@id` and `@type` for each node before populating its properties.
9.  **Partial Invalidation:** The `invalidate_uuid_plan_node` must be updated to support partial invalidation, allowing it to target specific records or entities for re-planning without destroying the entire plan.
10. **Empty Input Handling:** In the case of zero input records, the planner must return an empty `uuidPlan` and `slotTypeMap` to allow the workflow to complete gracefully with an empty graph.

## 5. Non-Goals (Out of Scope)

-   This is a backend-only feature. **No changes to the Streamlit UI** are required at this time.
-   Major refactoring of other agents (`ontology_researcher`, `custom_facet_node`, `hallucination_checker`) is not in scope. However, minor changes may be required for them to correctly integrate with the new planning state.

## 6. Design Considerations

-   This is a backend architectural change with no direct UI/UX impact.

## 7. Technical Considerations

-   The implementation will be guided by the detailed 10-step technical plan in `tasks/problems.txt`.
-   Key technologies to use are `uuid5` for deterministic IDs and `hashlib` (for SHA-256) for fingerprinting.
-   Primary files to be modified are `state.py`, `agents/uuid_planner.py`, `graph.py`, and `tools.py`.

## 8. Success Metrics

The success of this feature will be measured by the following:
-   A measurable reduction in ID-related validation errors during graph generation.
-   A noticeable performance improvement in workflows that involve data correction, as re-planning will be incremental.
-   Successful implementation and passing of all 10 acceptance tests outlined in `tasks/problems.txt`:
    1.  Determinism
    2.  Incremental Add
    3.  Update
    4.  Delete
    5.  Ontology Change
    6.  Zero Records
    7.  Relationships
    8.  (Implied) Structural validation passes
    9.  (Implied) Hallucination check passes
    10. (Implied) File-by-file changes are correctly implemented

## 9. Open Questions

-   None at this time. The technical plan is comprehensive. Any ambiguities should be clarified with the project lead before implementation.

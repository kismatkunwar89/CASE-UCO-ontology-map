from typing import List, Literal, Dict, Any
from typing_extensions import TypedDict
from pydantic.v1 import BaseModel, Field

# =============================================================================
# Data Models for Agent Outputs
# =============================================================================

class OntologyAnalysis(BaseModel):
    """Pydantic model for the structured ontology analysis data."""
    artifacts: List[str] = Field(default=[], description="List of identified artifact types.")
    classes: List[str] = Field(default=[], description="List of relevant CASE/UCO classes (observable objects).")
    facets: List[str] = Field(default=[], description="List of applicable facets (property bundles).")
    properties: Dict[str, List[str]] = Field(default={}, description="Dictionary mapping classes/facets to their relevant properties.")
    relationships: List[Dict[str, Any]] = Field(default=[], description="List of identified relationships between objects.")
    analysis: str = Field(default="", description="A 1-3 sentence summary of the mapping rationale.")
    additional_details: Dict[str, Any] = Field(default={}, description="Additional context, including unmapped elements.")

class ValidationResult(BaseModel):
    """Defines the structure for the output of the validator_node."""
    is_clean: bool = Field(
        description="Whether the JSON-LD is structurally valid")
    violations: List[str] = Field(
        default=[], description="List of validation violations")
    warnings: List[str] = Field(
        default=[], description="List of validation warnings")


class HallucinationResult(BaseModel):
    """Defines the structure for the output of the hallucination_check_node."""
    hallucinations_detected: Literal["yes", "no"] = Field(
        description="Whether hallucinations were detected")
    # ... (other fields)

# =============================================================================
# Schemas for Routing and Decisions
# =============================================================================


class Router(TypedDict):
    """Defines the schema for the supervisor's routing decision."""
    next: Literal[
        "ontology_research_node",
        "custom_facet_node",
        "graph_generator_node",
        "validator_node",
        "hallucination_check_node",
        "FINISH"
    ]


class ForensicHallucinationDetectionResult(BaseModel):
    """Structured output for forensic hallucination detection."""
    hallucinations_detected: Literal["yes", "no"]
    forensic_fidelity: Literal["yes", "no"]
    data_integrity: Literal["yes", "no"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    validation_decision: Literal["PASS", "REGENERATE"]
    hallucination_details: str
    corrections_needed: str

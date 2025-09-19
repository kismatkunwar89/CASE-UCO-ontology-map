# state.py

# =============================================================================
# Step 1: STATE DEFINITION
# =============================================================================
from typing import Dict, Any, List
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages

# --- Base State ---


class _BaseState(TypedDict):
    """The base state for the graph, managing the list of messages."""
    messages: Annotated[list, add_messages]

# --- Complete Workflow State ---


class State(_BaseState, total=False):
    """Represents the complete state of the agentic workflow."""
    # Core data fields
    ontologyMap: Dict[str, Any]
    ontologyMarkdown: str
    customFacets: Dict[str, Any]
    customState: Dict[str, Any]
    jsonldGraph: Dict[str, Any]

    # Loop control variables
    customFacetAttempts: int
    graphGeneratorAttempts: int
    validationAttempts: int
    layer2_attempts: int

    # Error and feedback fields
    customFacetErrors: List[str]
    graphGeneratorErrors: List[str]
    validationErrors: List[str]
    hallucinationErrors: List[str]

    # Validation system fields
    validation_result: Dict[str, Any]
    validation_feedback: str
    validationHistory: List[Dict[str, Any]]
    layer1_preserved_result: Dict[str, Any]
    use_fallback_result: bool

    # Layer 2 / Hallucination detection fields
    hallucination_result: Dict[str, Any]
    hallucination_feedback: str
    hallucinationAttempts: int
    hallucinationHistory: List[Dict[str, Any]]
    layer2_feedback_history: List[str]
    layer2_final_status: str

    # Memory Architecture Fields
    memory_patterns: Dict[str, Any]
    memory_knowledge: Dict[str, Any]
    memory_learning: Dict[str, Any]
    memory_context: str
    memory_persistence: Dict[str, Any]

    # Supervisor state tracking
    supervisor_decisions: List[str]
    current_worker: str
    workflow_stage: str
    learningContext: str

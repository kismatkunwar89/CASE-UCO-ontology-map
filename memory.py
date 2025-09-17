from typing import Dict, Any
from state import State

# =============================================================================
# Memory Management Functions
# =============================================================================


def load_memory_from_sessions(state: State) -> Dict[str, Any]:
    """Load memory from previous sessions (simulated)."""
    return state.get("memory_persistence", {
        "patterns": {}, "knowledge": {}, "learning": {}
    })


def save_memory_to_storage(state: State, memory_data: Dict[str, Any]) -> None:
    """Save memory to persistent storage (simulated)."""
    state["memory_persistence"] = memory_data


def learn_from_validation_result(state: State, validation_result: Dict[str, Any]) -> None:
    """Learn from validation results and update memory."""
    if not validation_result.get("is_clean", False):
        failure_pattern = extract_failure_pattern(validation_result)
        if failure_pattern:
            if "patterns" not in state.get("memory_patterns", {}):
                state["memory_patterns"] = {"patterns": {}}
            state["memory_patterns"]["patterns"][failure_pattern["type"]
                                                 ] = failure_pattern

            correction_strategy = generate_correction_pattern(failure_pattern)
            if correction_strategy:
                if "learning" not in state.get("memory_learning", {}):
                    state["memory_learning"] = {"learning": {}}
                state["memory_learning"]["learning"][failure_pattern["type"]
                                                     ] = correction_strategy


def extract_failure_pattern(validation_result: Dict[str, Any]) -> Dict[str, Any] | None:
    """Extract failure pattern from validation result."""
    violations = validation_result.get("violations")
    if not violations:
        return None

    pattern = {
        "type": "validation_failure",
        "violation_count": len(violations),
        "common_issues": [],
        "timestamp": validation_result.get("timestamp", "unknown")
    }

    for violation in violations:
        if "Message:" in violation:
            issue = violation.split("Message:")[-1].strip()
            pattern["common_issues"].append(issue)

    return pattern


def generate_correction_pattern(failure_pattern: Dict[str, Any]) -> Dict[str, Any]:
    """Generate correction pattern from failure pattern."""
    return {
        "strategy": "avoid_common_issues",
        "rules": failure_pattern["common_issues"],
        "priority": "high" if failure_pattern["violation_count"] > 2 else "medium"
    }


def update_memory_context(state: State) -> str:
    """Update memory context for the current session."""
    memory_data = load_memory_from_sessions(state)
    context_parts = []

    if memory_data.get("patterns"):
        context_parts.append("Previous failure patterns:")
        for pattern_type, pattern in memory_data["patterns"].items():
            context_parts.append(
                f"- {pattern_type}: {pattern.get('violation_count', 0)} violations")

    if memory_data.get("knowledge"):
        context_parts.append("Learned rules:")
        for rule_type, rule in memory_data["knowledge"].items():
            context_parts.append(f"- {rule_type}: {rule}")

    if memory_data.get("learning"):
        context_parts.append("Correction strategies:")
        for strategy_type, strategy in memory_data["learning"].items():
            context_parts.append(
                f"- {strategy_type}: {strategy.get('strategy', 'unknown')}")

    return "\n".join(context_parts) if context_parts else "No previous memory available"

"""
Shared utilities for categorizing validation and hallucination feedback.

This module provides common functions for separating "hard" feedback (critical issues
that require correction) from "soft" feedback (informational suggestions for improvement).
"""

from typing import List, Tuple


def categorize_validation_feedback(validation_report: str) -> Tuple[List[str], List[str]]:
    """
    Categorizes validation feedback into hard and soft feedback.

    Hard feedback (Violations, Warnings) should trigger self-correction.
    Soft feedback (Info) should be shown to users as suggestions.

    Args:
        validation_report: The validation report string from case_validate tool

    Returns:
        Tuple of (hard_feedback, soft_feedback) lists
    """
    hard_feedback = []
    soft_feedback = []

    if not validation_report or not isinstance(validation_report, str):
        return hard_feedback, soft_feedback

    # Split report into lines and process each
    lines = validation_report.split('\n')
    current_item = []
    current_severity = None

    for line in lines:
        line_stripped = line.strip()

        # Check for severity markers
        if 'Violation' in line or 'sh:Violation' in line:
            # Save previous item if exists
            if current_item and current_severity:
                item_text = '\n'.join(current_item).strip()
                if current_severity == 'hard':
                    hard_feedback.append(item_text)
                else:
                    soft_feedback.append(item_text)
            # Start new violation item
            current_item = [line]
            current_severity = 'hard'
        elif 'Warning' in line or 'sh:Warning' in line:
            # Save previous item if exists
            if current_item and current_severity:
                item_text = '\n'.join(current_item).strip()
                if current_severity == 'hard':
                    hard_feedback.append(item_text)
                else:
                    soft_feedback.append(item_text)
            # Start new warning item
            current_item = [line]
            current_severity = 'hard'
        elif 'Info' in line or 'sh:Info' in line:
            # Save previous item if exists
            if current_item and current_severity:
                item_text = '\n'.join(current_item).strip()
                if current_severity == 'hard':
                    hard_feedback.append(item_text)
                else:
                    soft_feedback.append(item_text)
            # Start new info item
            current_item = [line]
            current_severity = 'soft'
        elif line_stripped and current_severity:
            # Continue current item
            current_item.append(line)

    # Don't forget the last item
    if current_item and current_severity:
        item_text = '\n'.join(current_item).strip()
        if current_severity == 'hard':
            hard_feedback.append(item_text)
        else:
            soft_feedback.append(item_text)

    # If no severity markers found but report contains errors, treat as hard feedback
    if not hard_feedback and not soft_feedback and validation_report.strip():
        if any(keyword in validation_report.lower() for keyword in ['error', 'fail', 'invalid', 'incorrect']):
            hard_feedback.append(validation_report.strip())

    return hard_feedback, soft_feedback


def categorize_hallucination_feedback(
    hallucination_details: str,
    corrections_needed: str,
    severity_level: str
) -> Tuple[List[str], List[str]]:
    """
    Categorizes hallucination feedback into hard and soft feedback based on severity.

    Args:
        hallucination_details: Detailed description of detected hallucinations
        corrections_needed: Required corrections
        severity_level: One of "critical", "moderate", "informational"

    Returns:
        Tuple of (hard_feedback, soft_feedback) lists
    """
    hard_feedback = []
    soft_feedback = []

    # Combine details and corrections for complete feedback
    full_feedback = []
    if hallucination_details and hallucination_details.strip():
        full_feedback.append(f"Details: {hallucination_details}")
    if corrections_needed and corrections_needed.strip():
        full_feedback.append(f"Corrections: {corrections_needed}")

    feedback_text = "\n".join(full_feedback)

    if not feedback_text.strip():
        return hard_feedback, soft_feedback

    # Categorize based on severity level
    if severity_level == "critical":
        # Critical issues require immediate correction
        hard_feedback.append(feedback_text)
    elif severity_level == "moderate":
        # Moderate issues should be fixed but not as urgent
        hard_feedback.append(feedback_text)
    elif severity_level == "informational":
        # Informational observations are suggestions only
        soft_feedback.append(feedback_text)
    else:
        # Unknown severity - be conservative and treat as hard
        hard_feedback.append(feedback_text)

    return hard_feedback, soft_feedback


def format_feedback_for_display(feedback_list: List[str], category: str) -> str:
    """
    Formats a list of feedback items for display in UI or logs.

    Args:
        feedback_list: List of feedback strings
        category: Category name (e.g., "Structural", "Data Fidelity")

    Returns:
        Formatted string ready for display
    """
    if not feedback_list:
        return ""

    formatted = f"## {category} Feedback\n\n"
    for idx, item in enumerate(feedback_list, 1):
        formatted += f"{idx}. {item}\n\n"

    return formatted

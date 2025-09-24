import json
import re
from typing import Literal

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# --- Custom Module Imports ---
from state import State
from schemas import ForensicHallucinationDetectionResult
from utils import _get_input_artifacts, _msg_text

class FeedbackProcessingAgent:
    """A class to dynamically process hallucination feedback into actionable instructions."""

    def __init__(self, llm):
        self.llm = llm

    def analyze_feedback(self, feedback_list: list) -> str:
        if not feedback_list:
            return ""
        analysis_prompt = f"""You are a feedback analysis expert. Analyze the hallucination feedback below and create specific, actionable instructions for a JSON-LD generator.

Feedback to analyze:
{chr(10).join([f"- {fb}" for fb in feedback_list])}

Create clear, specific instructions to prevent these issues from recurring. Focus on:
1. What specific data to avoid
2. What properties to omit
3. What patterns to change
4. How to validate against original input

Return only the direct and specific instructions."""
        response = self.llm.invoke(analysis_prompt)
        return response.content

class DynamicCorrectionAgent:
    """A class to apply corrections to a JSON object based on dynamic analysis."""

    def __init__(self, llm):
        self.llm = llm

    def apply_corrections(self, json_obj: dict, feedback: str, original_input: str) -> dict:
        correction_prompt = f"""You are a JSON-LD correction expert. Fix the JSON-LD based on the provided hallucination feedback.

Original Input (The only source of truth):
{original_input}

Current JSON-LD:
{json.dumps(json_obj, indent=2)}

Hallucination Feedback:
{feedback}

Instructions:
1. Remove or modify ONLY the elements mentioned in the feedback.
2. Ensure every remaining value exists in the original input.
3. Return the corrected JSON-LD.
4. Do not add any new fabricated data.

Return only the corrected JSON-LD in a valid JSON format."""
        response = self.llm.invoke(correction_prompt)
        try:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response.content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            else:
                return json.loads(response.content)
        except json.JSONDecodeError:
            print("[WARNING] [Dynamic Correction] Could not parse corrected JSON, returning original object.")
            return json_obj

class ForensicHallucinationDetectionAgent:
    """LLM Agent that detects hallucinations in forensic JSON-LD output."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.structured_llm = self.llm.with_structured_output(
            ForensicHallucinationDetectionResult,
            method="function_calling"
        )

    def detect_hallucinations(self, input_artifacts: str, generated_output: str, user_query: str) -> ForensicHallucinationDetectionResult:
        print("[INFO] [Hallucination Agent] Analyzing for fabricated data...")
        prompt = f"""You are a forensic hallucination detection agent. Your task is to ensure data fidelity by detecting any values in the output that are not present in the original input.

CRITICAL RULES:
1. Every value in the JSON-LD output must be traceable to the original input.
2. No hardcoded paths, sizes, or fabricated data is allowed.
3. Ignore structural elements like @id, @context, @type, namespaces, and facet identifiers.

Analyze the JSON-LD output below and detect any hallucinations.

ORIGINAL INPUT ARTIFACTS:
{input_artifacts}

USER QUERY:
{user_query}

GENERATED JSON-LD OUTPUT:
{generated_output}"""
        try:
            result = self.structured_llm.invoke(prompt)
            print(f"[SUCCESS] [Hallucination Agent] Analysis complete: {result.validation_decision}")
            return result
        except Exception as e:
            print(f"[ERROR] [Hallucination Agent] LLM failed: {e}")
            return ForensicHallucinationDetectionResult(
                hallucinations_detected="yes",
                forensic_fidelity="no",
                data_integrity="no",
                confidence_score=0.0,
                validation_decision="REGENERATE",
                hallucination_details="Agent failed - assuming hallucinations present for safety.",
                corrections_needed="Manual review required due to detection failure."
            )

hallucination_agent = ForensicHallucinationDetectionAgent()

def hallucination_check_node(state: State) -> dict:
    """
    Performs Layer 2 validation for data hallucinations with a learning system.
    """
    print("[INFO] [Layer 2 Validation] Starting hallucination check...")

    if state.get("use_fallback_result", False):
        print("[INFO] [Hallucination Check] Fallback result is in use. Terminating step.")
        return {}

    current_attempts = state.get("layer2_attempts", 0)
    feedback_history = state.get("layer2_feedback_history", [])

    if current_attempts >= 2:
        print("[WARNING] [Layer 2] Max attempts reached. Using Layer 1 preserved result.")
        return {"use_fallback_result": True, "layer2_final_status": "FAILED_WITH_LEARNING"}

    input_artifacts = _get_input_artifacts(state)
    generated_output = json.dumps(state.get("jsonldGraph", {}))
    user_query = _msg_text(state.get("messages", [])) or _get_input_artifacts(state) or "Analyze the provided forensic artifacts."

    if not generated_output or generated_output == '{}':
        print("[ERROR] [Hallucination Check] No generated output found to check.")
        return {}

    result = hallucination_agent.detect_hallucinations(
        input_artifacts=input_artifacts,
        generated_output=generated_output,
        user_query=user_query
    )

    is_clean = result.hallucinations_detected == "no"

    update = {
        "hallucination_result": result.dict(),
        "layer2_attempts": current_attempts + 1,
        "l2_valid": bool(result.validation_decision == "PASS"),
    }

    if is_clean:
        update["hallucination_feedback"] = ""
    else:
        feedback = result.corrections_needed
        update["hallucination_feedback"] = feedback
        update["layer2_feedback_history"] = feedback_history + [feedback]
        if current_attempts + 1 >= 2:
            update["use_fallback_result"] = True
            update["layer2_final_status"] = "FAILED_WITH_LEARNING"
    
    return update

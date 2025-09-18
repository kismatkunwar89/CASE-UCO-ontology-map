"""
FastAPI routes for the forensic analysis API.
Defines endpoints for health checks and streaming analysis execution.
"""

import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services import execute_forensic_analysis_session_stream, generate_session_id

# Create API router
router = APIRouter()


class AnalysisInput(BaseModel):
    """Pydantic model for analysis input data."""
    user_identifier: str
    input_artifacts: str


class HealthResponse(BaseModel):
    """Pydantic model for health check response."""
    status: str
    message: str
    service: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API is running.

    Returns:
        HealthResponse: Status information about the API
    """
    return HealthResponse(
        status="healthy",
        message="Forensic Analysis API is running",
        service="case-uco-ontology-mapping-agent"
    )


@router.post("/invoke-streaming")
async def invoke_streaming_analysis(input_data: AnalysisInput):
    """
    Streaming endpoint for forensic analysis execution.

    Args:
        input_data: AnalysisInput containing user_identifier and input_artifacts

    Returns:
        StreamingResponse: Server-sent events stream with analysis progress

    Raises:
        HTTPException: If analysis fails to start
    """
    try:
        # Generate session ID
        session_id = generate_session_id(input_data.user_identifier)

        def generate_stream():
            """Generator function for streaming analysis events."""
            try:
                # Execute the analysis session with streaming
                for event in execute_forensic_analysis_session_stream(
                    session_id,
                    input_data.input_artifacts
                ):
                    # Format event as Server-Sent Event
                    event_data = {
                        "type": event["type"],
                        "session_id": event["session_id"],
                        "data": event
                    }

                    # Remove the session_id from data to avoid duplication
                    if "session_id" in event_data["data"]:
                        del event_data["data"]["session_id"]

                    # Format as SSE
                    yield f"data: {json.dumps(event_data)}\n\n"

                # Send completion event
                yield f"data: {json.dumps({'type': 'stream_complete', 'session_id': session_id})}\n\n"

            except Exception as e:
                # Send error event
                error_data = {
                    "type": "stream_error",
                    "session_id": session_id,
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "CASE/UCO Ontology Mapping Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "streaming_analysis": "/invoke-streaming"
        }
    }

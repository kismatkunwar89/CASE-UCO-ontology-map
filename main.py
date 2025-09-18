"""
FastAPI server entry point for the CASE/UCO Ontology Mapping Agent.
This is the new main.py that serves as the API server backend.
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our API routes
from routes import router

# Create FastAPI application
app = FastAPI(
    title="CASE/UCO Ontology Mapping Agent API",
    description="API for transforming unstructured digital forensics reports into structured JSON-LD graphs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize Phoenix tracing on app startup


@app.on_event("startup")
async def startup_event():
    # Initialize Phoenix tracing after server is ready
    import asyncio
    import threading

    def init_phoenix_sync():
        """Initialize Phoenix in a separate thread to avoid blocking"""
        try:
            from phoenix.otel import register

            os.environ["PHOENIX_API_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJBcGlLZXk6NSJ9.GFVSfOg--1GBYP9oiMSRF93J2Lq31H14pGOnk5pnQVo"

            tracer_provider = register(
                project_name="forensic-agent-system",
                endpoint="https://app.phoenix.arize.com/s/ktamsik101/v1/traces",
                auto_instrument=True
            )
            print("[INFO] Phoenix tracing is active.")

        except Exception as e:
            print(
                f"[WARNING] Phoenix initialization failed: {e} - continuing without tracing")

    # Start Phoenix initialization in background thread (non-blocking)
    phoenix_thread = threading.Thread(target=init_phoenix_sync, daemon=True)
    phoenix_thread.start()

    print("[INFO] Server startup complete - Phoenix initialization running in background")

# Configure CORS middleware to allow requests from Streamlit app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(router, prefix="/api/v1", tags=["analysis"])

# Root endpoint


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "CASE/UCO Ontology Mapping Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    # Run the server with uvicorn
    print("[INFO] Starting FastAPI server...")
    print("[INFO] API documentation available at: http://localhost:9000/docs")
    print("[INFO] Health check available at: http://localhost:9000/api/v1/health")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )

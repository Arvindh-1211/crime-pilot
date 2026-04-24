"""Main FastAPI application for NCRP Cybercrime Assistant."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import chat, complaint, upload, officer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # Startup: Initialize intent classifier
    from core.intent_classifier import intent_classifier

    try:
        intent_classifier.initialize()
        print("Intent classifier initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize intent classifier: {e}")

    # Startup: Initialize duplicate checker
    from core.duplicate_checker import duplicate_checker

    try:
        duplicate_checker.initialize()
        print("Duplicate checker initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize duplicate checker: {e}")

    yield

    # Shutdown (if needed for cleanup)
    print("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title="NCRP Cybercrime Assistant API",
    description="Intelligent chatbot for filing cybercrime complaints",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "NCRP Cybercrime Assistant",
        "version": "1.0.0",
        "description": "Intelligent chatbot for filing cybercrime complaints",
        "endpoints": {
            "chat": "/chat/start, /chat/message",
            "complaint": "/complaint/submit, /complaint/{id}",
            "upload": "/upload/evidence",
            "officer": "/officer/login, /officer/complaints"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(chat.router, prefix="/api/v1")
app.include_router(complaint.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(officer.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

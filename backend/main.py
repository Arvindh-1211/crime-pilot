"""Main FastAPI application for NCRP Cybercrime Assistant."""
print('main.py: imported os', flush=True)
import os
print('main.py: imported load_dotenv', flush=True)
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")
load_dotenv()
print('main.py: loaded dotenv', flush=True)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print('main.py: importing routes', flush=True)
from routes import chat, complaint, upload, officer
print('main.py: imported routes', flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown tasks."""
    # We've moved heavy initializations to be lazy-loaded or 
    # triggered only when the first chat starts to prevent 
    # blocking the Officer Portal login.
    print("NCRP Server started. AI models will be initialized on first use.")
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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173","http://127.0.0.0:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000","http://127.0.0.0:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
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

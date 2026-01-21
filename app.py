"""
FastAPI wrapper for Multi-Agent System - Simple & Secure
"""

from fastapi import FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from multi_agent_system import run_agent_system
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Multi-Agent System API",
    description="AI-powered multi-agent system with researcher, coder, and critic agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Security
API_KEY = os.getenv("API_KEY", "your-secret-api-key-here")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key from header"""
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key"
        )
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key


class QueryRequest(BaseModel):
    query: str = Field(..., description="The user query to process", min_length=1)


class QueryResponse(BaseModel):
    status: str
    user_request: str
    plan: dict
    researcher_output: str
    coder_output: str
    quality_score: float
    retry_attempts: int


@app.get("/health")
async def health_check():
    """
    Health check endpoint - no authentication required
    Checks if all services are connected properly
    """
    health_status = {
        "status": "healthy",
        "api": "running",
        "groq_api_key": "configured" if os.getenv("GROQ_API_KEY") else "missing",
        "tavily_api_key": "configured" if os.getenv("TAVILY_API_KEY") else "missing",
        "langsmith_tracing": "enabled" if os.getenv("LANGCHAIN_TRACING_V2") == "true" else "disabled"
    }
    
    # Check if critical services are configured
    if not os.getenv("GROQ_API_KEY"):
        health_status["status"] = "unhealthy"
        health_status["error"] = "GROQ_API_KEY not configured"
    
    return health_status


@app.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    api_key: str = Security(verify_api_key)
):
    """
    Process a query through the multi-agent system
    Requires API Key authentication via X-API-Key header
    """
    try:
        result = run_agent_system(request.query)
        
        final_output = json.loads(result.get("final_output", "{}"))
        
        return QueryResponse(
            status="success",
            user_request=final_output.get("user_request", ""),
            plan=final_output.get("plan", {}),
            researcher_output=final_output.get("researcher_output", ""),
            coder_output=final_output.get("coder_output", ""),
            quality_score=final_output.get("quality_score", 0.0),
            retry_attempts=final_output.get("retry_attempts", 0)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
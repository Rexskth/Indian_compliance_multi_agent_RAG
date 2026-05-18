import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from backend.agents.orchestrator import orchestrator
from backend.ingestion.config import config


app = FastAPI(
    title="Indian Compliance RAG API",
    description="Multi-agent RAG system for Indian legal compliance",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class QueryResponse(BaseModel):
    answer: str
    citations: List[Dict]
    risk_level: str
    severity_score: float
    risk_details: Dict
    confidence: float
    intent: str
    sources: List[str]


class HealthResponse(BaseModel):
    status: str
    version: str
    collection_count: int


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    from backend.ingestion.vector_store import VectorStore
    vs = VectorStore()
    collection = vs.get_or_create_collection()
    count = collection.count()

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        collection_count=count
    )


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        result = orchestrator.process_query(
            query=request.query,
            conversation_history=request.conversation_history
        )

        return QueryResponse(
            answer=result["answer"],
            citations=result["citations"],
            risk_level=result["risk_level"],
            severity_score=result.get("severity_score", 0.0),
            risk_details=result.get("risk_details", {}),
            confidence=result["confidence"],
            intent=result["intent"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics")
async def metrics():
    return {
        "retrieval": {
            "vector_weight": config.VECTOR_WEIGHT,
            "bm25_weight": config.BM25_WEIGHT,
            "top_k": config.TOP_K
        },
        "chunking": {
            "chunk_size": config.CHUNK_SIZE,
            "chunk_overlap": config.CHUNK_OVERLAP
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
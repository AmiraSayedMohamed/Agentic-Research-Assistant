
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import uuid
import json
from datetime import datetime
import logging
from agents.coral_orchestrator import CoralOrchestrator
from agents.pdf_upload_handler import PDFUploadHandler
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from agents.summary_agent import SummaryAgent
from agents.voice_agent import text_to_speech



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

orchestrator = None
pdf_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global orchestrator, pdf_handler
    nebius_api_key = os.getenv("NEBIUS_API_KEY")
    if not nebius_api_key:
        logger.warning("NEBIUS_API_KEY not found - using mock responses")
    
    orchestrator = CoralOrchestrator(nebius_api_key)
    await orchestrator.initialize_agents()
    
    # Initialize PDF handler
    pdf_handler = PDFUploadHandler(
        upload_dir="uploads",
        nebius_api_key=nebius_api_key
    )
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown")

app = FastAPI(
    title="Agentic Research Assistant API", 
    version="1.0.0",
    lifespan=lifespan
)

# Crossmint NFT minting endpoint
from agents.crossmint_agent import mint_nft
@app.post("/mint_nft")
async def mint_nft_endpoint(request: Request):
    metadata = await request.json()
    result = mint_nft(metadata)
    return result

# Voice synthesis endpoint
@app.post("/synthesize_voice")
async def synthesize_voice(request: Request):
    data = await request.json()
    text = data.get("text")
    voice = data.get("voice", "Rachel")
    audio_bytes = text_to_speech(text, voice)
    return StreamingResponse(iter([audio_bytes]), media_type="audio/mpeg")


@app.post("/summarize")
async def summarize_endpoint(request: Request):
    data = await request.json()
    papers = data.get("papers", [])
    query = data.get("query", "")
    agent = SummaryAgent(api_key=os.getenv("NEBIUS_API_KEY"))
    async with agent as summary_agent:
        summaries = await summary_agent.summarize_papers(papers, query)
    return {"summaries": summaries}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ResearchQuery(BaseModel):
    query: str
    max_papers: int = 10
    include_pdf: bool = False
    pay: bool = False

class ResearchJob(BaseModel):
    job_id: str
    status: str
    progress: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class PaperSummary(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    summary: str
    relevance_score: float
    doi: Optional[str] = None
    url: Optional[str] = None

class SynthesizedReport(BaseModel):
    executive_summary: str
    themes: List[Dict[str, str]]
    gaps: List[Dict[str, Any]]
    recommendations: List[str]
    citations: List[str]
    full_text: str

# In-memory storage (use Redis/Database in production)
research_jobs: Dict[str, ResearchJob] = {}

# API Endpoints
@app.post("/research")
async def start_research(query: ResearchQuery, background_tasks: BackgroundTasks):
    """Start a new research job using Coral Protocol orchestration"""
    job_id = str(uuid.uuid4())
    
    job = ResearchJob(
        job_id=job_id,
        status="started",
        progress={
            "search": {"status": "pending", "message": "Initializing search"},
            "summary": {"status": "pending", "message": "Waiting for search"},
            "synthesis": {"status": "pending", "message": "Waiting for summaries"},
            "voice": {"status": "pending", "message": "Waiting for synthesis"},
            "monetization": {"status": "pending", "message": "Waiting for completion"}
        },
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    research_jobs[job_id] = job
    
    # Start background processing with Coral orchestrator
    background_tasks.add_task(process_research_job_with_coral, job_id, query)
    
    return {"job_id": job_id, "status": "started"}

async def process_research_job_with_coral(job_id: str, query: ResearchQuery):
    """Process research job using Coral Protocol orchestration"""
    try:
        job = research_jobs[job_id]
        
        # Execute workflow through Coral orchestrator
        results = await orchestrator.execute_research_workflow(
            query.query, 
            query.max_papers, 
            job_id
        )
        
        # Update job with results
        job.results = results
        job.status = "completed"
        job.updated_at = datetime.now()
        
        # Update progress to completed
        for step in job.progress:
            job.progress[step]["status"] = "completed"
        
        logger.info(f"Research job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing research job {job_id}: {str(e)}")
        job.status = "error"
        job.progress["error"] = {"message": str(e)}
        job.updated_at = datetime.now()

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get research job status with enhanced Coral Protocol tracking"""
    if job_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = research_jobs[job_id]
    
    # Get detailed workflow status from orchestrator if available
    workflow_status = None
    if orchestrator:
        workflow_status = orchestrator.get_workflow_status(job_id)
    
    return {
        "job_id": job_id,
        "status": job.status,
        "progress": job.progress,
        "workflow_details": workflow_status,
        "results": job.results,
        "created_at": job.created_at,
        "updated_at": job.updated_at
    }

@app.post("/rephrase")
async def rephrase_text(text: str, style: str = "humanize"):
    """Rephrase text for humanization or paraphrasing"""
    await asyncio.sleep(1)  # Simulate processing
    
    variants = [
        f"Rephrased variant 1: {text}",
        f"Rephrased variant 2: {text}",
        f"Rephrased variant 3: {text}"
    ]
    
    return {
        "original": text,
        "variants": variants,
        "human_scores": [92, 89, 95],  # Mock scores
        "style": style
    }

@app.post("/plagiarism_check")
async def check_plagiarism(text: str, sources: Optional[List[str]] = None):
    """Check text for plagiarism against sources"""
    await asyncio.sleep(1)  # Simulate processing
    
    return {
        "overall_risk": "Low (8%)",
        "flagged_sections": [
            {
                "text": "Introduction paragraph excerpt",
                "similarity_score": 0.12,
                "source_paper_id": "1",
                "source_title": "Quantum Computing Ethics: A Comprehensive Framework"
            }
        ],
        "human_score": 92
    }

@app.get("/")
async def root():
    """API health check"""
    return {"message": "Agentic Research Assistant API", "status": "healthy"}

# PDF upload and analysis endpoints
@app.post("/upload_pdf")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    query: str = Form(...),
    user_id: Optional[str] = Form(None)
):
    """Upload and analyze PDF file"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Process upload and analysis
        result = await pdf_handler.handle_pdf_upload(
            file_content, 
            file.filename, 
            query, 
            user_id
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return {
            "success": True,
            "message": "PDF uploaded and analyzed successfully",
            "analysis_result": result['analysis_result'],
            "file_info": result['file_info']
        }
        
    except Exception as e:
        logger.error(f"PDF upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pdf_highlights/{file_id}")
async def get_pdf_highlights(file_id: str, sentence_ids: str):
    """Get PDF highlights for specific sentences"""
    try:
        # Parse sentence IDs
        ids = [int(id.strip()) for id in sentence_ids.split(',') if id.strip().isdigit()]
        
        # Mock file path (in production, retrieve from database)
        file_path = f"uploads/{file_id}.pdf"
        
        result = await pdf_handler.get_pdf_highlights(file_path, ids)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid sentence IDs format")
    except Exception as e:
        logger.error(f"Failed to get PDF highlights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search_pdf")
async def search_pdf_content(file_id: str, query: str, top_k: int = 10):
    """Search PDF content using RAG pipeline"""
    try:
        # Mock file path (in production, retrieve from database)
        file_path = f"uploads/{file_id}.pdf"
        
        result = await pdf_handler.search_pdf_content(file_path, query, top_k)
        
        if not result['success']:
            raise HTTPException(status_code=404, detail=result['error'])
        
        return result
        
    except Exception as e:
        logger.error(f"PDF search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pdf_stats")
async def get_pdf_upload_stats():
    """Get PDF upload statistics"""
    try:
        stats = pdf_handler.get_upload_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get PDF stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

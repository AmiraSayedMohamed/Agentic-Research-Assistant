from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import uuid, asyncio
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
import tempfile
from datetime import datetime
import logging
import io
from agents.coral_orchestrator import CoralOrchestrator
from agents.pdf_upload_handler import PDFUploadHandler
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from agents.research_agents import (
    ResearchOrchestrator,
    ResearchResult,
    Paper,
    PaperSummary
)



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

orchestrator = None
pdf_handler = None

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Startup
        global orchestrator, pdf_handler
        nebius_api_key = os.getenv("NEBIUS_API_KEY")
        if not nebius_api_key:
            logger.warning("NEBIUS_API_KEY not found - using mock responses")

        # Commented out agent initializations for debugging
        # Skip orchestrator initialization for now to avoid startup hangs
        orchestrator = None
        logger.info("Orchestrator initialization skipped for faster startup")
        pdf_handler = PDFUploadHandler(
            upload_dir=os.path.join(os.path.dirname(__file__), "uploads"),
            nebius_api_key=nebius_api_key
        )

        logger.info("Application startup complete")
        yield
        # Shutdown
        logger.info("Application shutdown")
    except Exception as e:
        logger.error(f"Error during lifespan startup: {e}")
        raise


# Initialize global variables
orchestrator = None
pdf_handler = None

app = FastAPI(
    title="Agentic Research Assistant API", 
    version="1.0.0"
)

# Initialize PDF handler on first request
@app.on_event("startup")
async def startup_event():
    global pdf_handler
    try:
        nebius_api_key = os.getenv("NEBIUS_API_KEY")
        pdf_handler = PDFUploadHandler(
            upload_dir=os.path.join(os.path.dirname(__file__), "uploads"),
            nebius_api_key=nebius_api_key
        )
        logger.info("PDF handler initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PDF handler: {e}")
# ========== Chatbot PDF Q&A Endpoint ========== 
class ChatPDFRequest(BaseModel):
    question: str
    paper_id: str = None

@app.post("/api/chat_pdf")
async def chat_pdf_endpoint(request: ChatPDFRequest):
    # Use the PDFUploadHandler (initialized at app startup) so we reuse the same
    # extraction/index built during upload processing. This avoids loading/encoding
    # the PDF again here and provides consistent behavior.
    try:
        if not pdf_handler:
            raise RuntimeError("PDF handler not initialized on server")

        # Locate latest uploaded PDF in the backend uploads directory
        pdf_dir = os.path.join(os.path.dirname(__file__), "uploads")
        if not os.path.isdir(pdf_dir):
            return {"answer": "No uploaded PDFs directory found on server."}

        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            return {"answer": "No PDF uploaded."}

        pdf_files_sorted = sorted(pdf_files, reverse=True)
        pdf_path = os.path.join(pdf_dir, pdf_files_sorted[0])

        # Ensure analyzer is initialized and has embeddings/index (if available)
        if not pdf_handler.pdf_analyzer:
            return {"answer": "PDF analyzer is not initialized. Please upload a PDF first."}

        # Use the analyzer's ask_question method which includes Gemini LLM integration
        try:
            # Use ask_question method which does RAG + Gemini synthesis
            result = await pdf_handler.pdf_analyzer.ask_question(request.question, top_k=8)
            
            if result.get('answer'):
                return {
                    "answer": result['answer'],
                    "sources": result.get('sources', []),
                    "context": result.get('context', '')
                }
            else:
                return {"answer": "No relevant information found in the uploaded PDF."}
                
        except Exception as e:
            logger.exception("Error during PDF question answering")
            return {"answer": f"Error while processing question: {str(e)}"}

    except Exception as e:
        logger.exception("chat_pdf endpoint error")
        raise HTTPException(status_code=500, detail=str(e))

# Add CORS middleware for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Research Paper Search Endpoints ==========
class ResearchRequest(BaseModel):
    query: str
    max_results: int = 5
    min_year: Optional[int] = None
    user_email: Optional[str] = None
    options: Optional[Dict[str, bool]] = None

class ResearchStatus(BaseModel):
    job_id: str
    status: str
    progress: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None

# Initialize research orchestrator
research_orchestrator = None

@app.post("/api/research/start")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Start a new research paper search and analysis job"""
    global research_orchestrator
    
    try:
        # Initialize orchestrator if not already done
        if not research_orchestrator:
            nebius_api_key = os.getenv("NEBIUS_API_KEY")
            gemini_api_key = os.getenv("GOOGLE_API_KEY")
            
            if not nebius_api_key:
                raise HTTPException(status_code=500, detail="NEBIUS_API_KEY not configured")
            
            research_orchestrator = ResearchOrchestrator(nebius_api_key, gemini_api_key)
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        job_status = {
            "job_id": job_id,
            "status": "started",
            "progress": {
                "search": {"status": "pending", "message": "Initializing paper search"},
                "summary": {"status": "pending", "message": "Waiting for search results"},
                "synthesis": {"status": "pending", "message": "Waiting for summaries"},
                "voice": {"status": "pending", "message": "Waiting for synthesis"},
                "monetization": {"status": "pending", "message": "Waiting for completion"}
            },
            "results": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Store job status
        research_jobs[job_id] = job_status
        
        # Start background processing
        background_tasks.add_task(process_research_job, job_id, request)
        
        return {"job_id": job_id, "status": "started", "message": "Research job started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start research job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_research_job(job_id: str, request: ResearchRequest):
    """Process research job using the new research orchestrator"""
    try:
        job = research_jobs[job_id]
        
        # Update job status to processing
        job["status"] = "processing"
        job["updated_at"] = datetime.now().isoformat()
        
        # Set default options if not provided
        options = request.options or {
            'use_summary': True,
            'use_synthesis': True,
            'use_voice': False,
            'use_nft': False
        }
        
        # Execute research workflow
        logger.info(f"Starting research for job {job_id}: {request.query}")
        
        result = await research_orchestrator.conduct_research(
            query=request.query,
            max_results=request.max_results,
            min_year=request.min_year,
            user_email=request.user_email,
            options=options
        )
        
        # Convert result to serializable format
        serializable_result = {
            "query": result.query,
            "papers": [
                {
                    "title": p.title,
                    "authors": p.authors,
                    "abstract": p.abstract,
                    "url": p.url,
                    "publication_year": p.publication_year,
                    "source_db": p.source_db
                } for p in result.papers
            ],
            "summaries": [
                {
                    "original_paper": {
                        "title": s.original_paper.title,
                        "authors": s.original_paper.authors,
                        "publication_year": s.original_paper.publication_year,
                        "source_db": s.original_paper.source_db
                    },
                    "summary_text": s.summary_text
                } for s in result.summaries
            ],
            "synthesized_report": result.synthesized_report,
            "has_audio": result.audio_bytes is not None,
            "nft_status": result.nft_status,
            "email_status": result.email_status
        }
        
        # Update job with results
        job["results"] = serializable_result
        job["status"] = "completed"
        job["updated_at"] = datetime.now().isoformat()
        
        # Update all progress steps to completed
        for step in job["progress"]:
            job["progress"][step]["status"] = "completed"
            job["progress"][step]["message"] = "Completed successfully"
        
        logger.info(f"Research job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing research job {job_id}: {str(e)}")
        job["status"] = "error"
        job["progress"]["error"] = {"message": str(e)}
        job["updated_at"] = datetime.now().isoformat()

@app.get("/api/research/status/{job_id}")
async def get_research_status(job_id: str):
    """Get research job status and results"""
    if job_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Research job not found")
    
    return research_jobs[job_id]

@app.post("/api/research/audio/{job_id}")
async def get_research_audio(job_id: str):
    """Get audio presentation for completed research job"""
    if job_id not in research_jobs:
        raise HTTPException(status_code=404, detail="Research job not found")
    
    job = research_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Research job not completed yet")
    
    # Generate audio from synthesized report if not already done
    try:
        global research_orchestrator
        if not research_orchestrator:
            raise HTTPException(status_code=500, detail="Research orchestrator not initialized")
        
        report = job["results"]["synthesized_report"]
        audio_bytes = await research_orchestrator.voice_agent.present(report)
        
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        
        return StreamingResponse(
            io.BytesIO(audio_bytes), 
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=research_report.mp3"}
        )
        
    except Exception as e:
        logger.error(f"Failed to generate audio for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Crossmint NFT minting endpoint
try:
    from agents.crossmint_agent import mint_nft
    @app.post("/mint_nft")
    async def mint_nft_endpoint(request: Request):
        metadata = await request.json()
        result = mint_nft(metadata)
        return result
except ImportError:
    logger.warning("Crossmint agent not available - NFT minting disabled")

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

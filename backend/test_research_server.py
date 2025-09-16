"""
Research-enabled FastAPI server for testing
Includes both PDF chat and research functionality
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import logging
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Import our research agents
from agents.research_agents import ResearchOrchestrator, ResearchResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Agentic Research Assistant API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ResearchRequest(BaseModel):
    query: str
    max_results: int = 5
    min_year: Optional[int] = None
    user_email: Optional[str] = None
    options: Optional[Dict[str, bool]] = None

class ChatPDFRequest(BaseModel):
    question: str
    paper_id: Optional[str] = None

# Global variables
research_orchestrator = None
research_jobs: Dict[str, Dict] = {}

@app.get("/")
async def root():
    return {"message": "Agentic Research Assistant API", "status": "healthy"}

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
            logger.info("Research orchestrator initialized")
        
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
        
        logger.info(f"Started research job {job_id} for query: {request.query}")
        return {"job_id": job_id, "status": "started", "message": "Research job started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start research job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_research_job(job_id: str, request: ResearchRequest):
    """Process research job using the research orchestrator"""
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
    
    # Generate audio from synthesized report
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

# PDF Chat endpoint (keeping existing functionality)
@app.post("/api/chat_pdf")
async def chat_pdf_endpoint(request: ChatPDFRequest):
    """Chat with uploaded PDF"""
    try:
        from agents.pdf_upload_handler import PDFUploadHandler
        
        # Find latest PDF
        pdf_dir = os.path.join(os.path.dirname(__file__), "uploads")
        if not os.path.isdir(pdf_dir):
            return {"answer": "No uploaded PDFs directory found on server."}

        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            return {"answer": "No PDF uploaded. Please upload a PDF first."}

        pdf_files_sorted = sorted(pdf_files, reverse=True)
        pdf_path = os.path.join(pdf_dir, pdf_files_sorted[0])
        
        logger.info(f"Using PDF: {pdf_path}")

        # Initialize handler with Google API key for Gemini
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            return {"answer": "Google API key not found. Please set GOOGLE_API_KEY in environment."}
            
        pdf_handler = PDFUploadHandler(
            upload_dir=pdf_dir,
            nebius_api_key=os.getenv("NEBIUS_API_KEY")
        )
        
        # Initialize the PDF analyzer and build FAISS index if needed
        await pdf_handler.pdf_analyzer.initialize_embeddings()
        
        # Check if we need to analyze the PDF (build FAISS index)
        if not hasattr(pdf_handler.pdf_analyzer, 'faiss_index') or pdf_handler.pdf_analyzer.faiss_index is None:
            logger.info(f"Building FAISS index for PDF: {pdf_path}")
            analysis_result = await pdf_handler.pdf_analyzer.analyze_pdf(pdf_path)
            logger.info(f"FAISS index built with {len(pdf_handler.pdf_analyzer.sentence_metadata)} sentences")
        
        # Check if analyzer exists and has index
        if not pdf_handler.pdf_analyzer:
            return {"answer": "PDF analyzer failed to initialize."}
            
        if not hasattr(pdf_handler.pdf_analyzer, 'faiss_index') or pdf_handler.pdf_analyzer.faiss_index is None:
            return {"answer": "Failed to build FAISS index from PDF."}

        # Test the ask_question method with Gemini integration
        logger.info(f"Calling ask_question with: {request.question}")
        result = await pdf_handler.pdf_analyzer.ask_question(request.question, top_k=8)
        
        logger.info(f"Gemini result: {result}")
        
        if result.get('answer'):
            return {
                "answer": result['answer'],
                "sources": result.get('sources', []),
                "context": result.get('context', ''),
                "gemini_called": True,
                "pdf_used": os.path.basename(pdf_path)
            }
        else:
            return {"answer": "No relevant information found in the uploaded PDF."}
            
    except Exception as e:
        logger.exception("Error in chat_pdf endpoint")
        return {"answer": f"Error: {str(e)}", "error_type": type(e).__name__}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
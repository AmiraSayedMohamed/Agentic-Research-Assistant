"""
Agentic Research Assistant - FastAPI Backend
Multi-agent system for academic research assistance
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import logging

from .orchestrator import AgentOrchestrator
from .models.schemas import ResearchQuery, ResearchResult, PaperSummary, SynthesisReport

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Research Assistant",
    description="Multi-agent system for academic research",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = AgentOrchestrator()

@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup"""
    logger.info("Starting Agentic Research Assistant...")
    await orchestrator.initialize()
    logger.info("System initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Agentic Research Assistant...")
    await orchestrator.cleanup()
    logger.info("Shutdown complete")

@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "Agentic Research Assistant API",
        "version": "1.0.0",
        "status": "active",
        "agents": [
            "Research Agent",
            "Summary Agent", 
            "Synthesis Agent",
            "Presentation Agent"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

@app.post("/research", response_model=ResearchResult)
async def conduct_research(query: ResearchQuery, background_tasks: BackgroundTasks):
    """
    Main research endpoint that orchestrates the multi-agent workflow
    
    Args:
        query: Research query with parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        ResearchResult: Complete research results with papers, summaries, and synthesis
    """
    try:
        logger.info(f"Received research query: {query.query}")
        
        # Execute multi-agent research workflow
        result = await orchestrator.execute_research_workflow(query)
        
        logger.info(f"Research completed successfully for query: {query.query}")
        return result
        
    except Exception as e:
        logger.error(f"Research workflow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@app.post("/search-papers")
async def search_papers(query: ResearchQuery):
    """
    Search for papers using Research Agent only
    
    Args:
        query: Search parameters
        
    Returns:
        List of papers found
    """
    try:
        papers = await orchestrator.research_agent.search_papers(
            query.query, 
            max_results=query.max_papers
        )
        return {"papers": papers}
        
    except Exception as e:
        logger.error(f"Paper search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/summarize-paper")
async def summarize_paper(paper_id: str):
    """
    Summarize a specific paper using Summary Agent
    
    Args:
        paper_id: Identifier for the paper to summarize
        
    Returns:
        PaperSummary: Structured summary of the paper
    """
    try:
        summary = await orchestrator.summary_agent.summarize_paper(paper_id)
        return summary
        
    except Exception as e:
        logger.error(f"Paper summarization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@app.post("/synthesize-research")
async def synthesize_research(paper_ids: List[str]):
    """
    Synthesize findings across multiple papers using Synthesis Agent
    
    Args:
        paper_ids: List of paper identifiers to synthesize
        
    Returns:
        SynthesisReport: Cross-paper synthesis and analysis
    """
    try:
        synthesis = await orchestrator.synthesis_agent.synthesize_papers(paper_ids)
        return synthesis
        
    except Exception as e:
        logger.error(f"Research synthesis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")

@app.get("/research-history")
async def get_research_history():
    """Get history of previous research queries"""
    try:
        history = await orchestrator.get_research_history()
        return {"history": history}
    except Exception as e:
        logger.error(f"Failed to retrieve research history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

@app.delete("/research-history/{query_id}")
async def delete_research_entry(query_id: str):
    """Delete a specific research entry from history"""
    try:
        await orchestrator.delete_research_entry(query_id)
        return {"message": "Research entry deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete research entry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
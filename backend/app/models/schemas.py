"""
Pydantic schemas for the Agentic Research Assistant API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PaperSource(str, Enum):
    """Enumeration of paper sources"""
    ARXIV = "arxiv"
    PUBMED = "pubmed" 
    DOAJ = "doaj"
    CROSSREF = "crossref"

class ResearchQuery(BaseModel):
    """Schema for research query input"""
    query: str = Field(..., description="Research query string", min_length=3, max_length=500)
    max_papers: Optional[int] = Field(default=10, description="Maximum number of papers to retrieve", ge=1, le=50)
    date_range: Optional[Dict[str, str]] = Field(default=None, description="Date range for papers (start_date, end_date)")
    sources: Optional[List[PaperSource]] = Field(default=None, description="Specific sources to search")
    include_preprints: Optional[bool] = Field(default=True, description="Include preprint papers")
    language: Optional[str] = Field(default="en", description="Language filter")

class Author(BaseModel):
    """Schema for paper author"""
    name: str
    affiliation: Optional[str] = None
    email: Optional[str] = None

class Paper(BaseModel):
    """Schema for academic paper"""
    id: str = Field(..., description="Unique paper identifier")
    title: str
    authors: List[Author]
    abstract: str
    doi: Optional[str] = None
    url: str
    source: PaperSource
    published_date: datetime
    citation_count: Optional[int] = 0
    keywords: Optional[List[str]] = None
    pdf_url: Optional[str] = None

class PaperSummary(BaseModel):
    """Schema for paper summary"""
    paper_id: str
    title: str
    authors: List[str]
    
    # Structured summary components
    objective: str = Field(..., description="Main research objective")
    methodology: str = Field(..., description="Research methodology used")
    key_findings: List[str] = Field(..., description="Main findings and results")
    conclusions: str = Field(..., description="Authors' conclusions")
    limitations: Optional[str] = Field(default=None, description="Study limitations")
    
    # Metadata
    summary_generated_at: datetime
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
class SynthesisTheme(BaseModel):
    """Schema for synthesis theme"""
    theme: str
    description: str
    supporting_papers: List[str]  # Paper IDs
    evidence_strength: str  # "strong", "moderate", "weak"

class ResearchGap(BaseModel):
    """Schema for identified research gap"""
    gap_description: str
    related_themes: List[str]
    potential_impact: str  # "high", "medium", "low"
    suggested_research_directions: List[str]

class SynthesisReport(BaseModel):
    """Schema for synthesis report across multiple papers"""
    query: str
    paper_ids: List[str]
    total_papers: int
    
    # Synthesis content
    executive_summary: str
    main_themes: List[SynthesisTheme]
    consensus_findings: List[str]
    conflicting_results: List[str]
    research_gaps: List[ResearchGap]
    methodology_analysis: str
    
    # Metadata
    generated_at: datetime
    synthesis_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class PresentationFormat(str, Enum):
    """Available presentation formats"""
    STRUCTURED_REPORT = "structured_report"
    EXECUTIVE_SUMMARY = "executive_summary"
    BULLET_POINTS = "bullet_points"
    ACADEMIC_PAPER = "academic_paper"

class ResearchResult(BaseModel):
    """Complete research result from multi-agent workflow"""
    query: ResearchQuery
    
    # Results from each agent
    papers_found: List[Paper]
    paper_summaries: List[PaperSummary]
    synthesis_report: SynthesisReport
    
    # Formatted presentation
    formatted_report: str
    presentation_format: PresentationFormat
    
    # Metadata
    processing_time_seconds: float
    total_tokens_used: Optional[int] = None
    research_id: str
    created_at: datetime

class ResearchHistoryEntry(BaseModel):
    """Schema for research history entry"""
    research_id: str
    query: str
    papers_count: int
    created_at: datetime
    processing_time: float
    status: str  # "completed", "failed", "in_progress"

class AgentStatus(BaseModel):
    """Schema for individual agent status"""
    agent_name: str
    status: str  # "idle", "processing", "error"
    current_task: Optional[str] = None
    last_activity: datetime

class SystemStatus(BaseModel):
    """Schema for overall system status"""
    system_health: str  # "healthy", "degraded", "error"
    active_research_count: int
    agent_statuses: List[AgentStatus]
    cache_hit_rate: Optional[float] = None
    average_response_time: Optional[float] = None

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str
    detail: str
    timestamp: datetime
    request_id: Optional[str] = None
"""
Agent Orchestrator - Coordinates the multi-agent research workflow
"""

import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from .models.schemas import (
    ResearchQuery, ResearchResult, Paper, PaperSummary, 
    SynthesisReport, PresentationFormat, ResearchHistoryEntry
)
from .agents.research_agent import ResearchAgent
from .agents.summary_agent import SummaryAgent
from .agents.synthesis_agent import SynthesisAgent
from .agents.presentation_agent import PresentationAgent
from .database.research_database import ResearchDatabase

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates the multi-agent research workflow"""
    
    def __init__(self):
        # Initialize agents
        self.research_agent = ResearchAgent()
        self.summary_agent = SummaryAgent()
        self.synthesis_agent = SynthesisAgent()
        self.presentation_agent = PresentationAgent()
        
        # Initialize database
        self.database = ResearchDatabase()
        
        # Workflow state tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self):
        """Initialize all agents and database"""
        logger.info("Initializing Agent Orchestrator...")
        
        # Initialize database first
        await self.database.initialize()
        
        # Initialize all agents
        await asyncio.gather(
            self.research_agent.initialize(),
            self.summary_agent.initialize(),
            self.synthesis_agent.initialize(),
            self.presentation_agent.initialize()
        )
        
        logger.info("Agent Orchestrator initialized successfully")
    
    async def cleanup(self):
        """Cleanup all agents and database"""
        logger.info("Cleaning up Agent Orchestrator...")
        
        # Cleanup agents
        await asyncio.gather(
            self.research_agent.cleanup(),
            self.summary_agent.cleanup(),
            self.synthesis_agent.cleanup(),
            self.presentation_agent.cleanup()
        )
        
        # Cleanup database
        await self.database.cleanup()
        
        logger.info("Agent Orchestrator cleanup complete")
    
    async def execute_research_workflow(self, query: ResearchQuery) -> ResearchResult:
        """
        Execute the complete multi-agent research workflow
        
        Args:
            query: Research query with parameters
            
        Returns:
            ResearchResult with complete analysis
        """
        research_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting research workflow {research_id} for query: '{query.query}'")
        
        try:
            # Track workflow state
            self.active_workflows[research_id] = {
                "status": "in_progress",
                "current_step": "research",
                "start_time": start_time
            }
            
            # Step 1: Research Phase - Find relevant papers
            logger.info(f"[{research_id}] Phase 1: Searching for papers...")
            papers = await self.research_agent.search_papers(
                query.query,
                max_results=query.max_papers,
                sources=query.sources
            )
            
            if not papers:
                raise ValueError("No papers found for the given query")
            
            self.active_workflows[research_id]["current_step"] = "summarization"
            self.active_workflows[research_id]["papers_found"] = len(papers)
            
            # Step 2: Summary Phase - Summarize each paper
            logger.info(f"[{research_id}] Phase 2: Summarizing {len(papers)} papers...")
            summaries = await self.summary_agent.summarize_papers_batch(papers)
            
            if not summaries:
                raise ValueError("Failed to generate summaries for papers")
            
            self.active_workflows[research_id]["current_step"] = "synthesis"
            self.active_workflows[research_id]["summaries_created"] = len(summaries)
            
            # Step 3: Synthesis Phase - Synthesize findings across papers
            logger.info(f"[{research_id}] Phase 3: Synthesizing findings across {len(summaries)} papers...")
            synthesis_report = await self.synthesis_agent.synthesize_papers(summaries, query.query)
            
            self.active_workflows[research_id]["current_step"] = "presentation"
            
            # Step 4: Presentation Phase - Format results
            logger.info(f"[{research_id}] Phase 4: Formatting results...")
            formatted_report = await self.presentation_agent.format_research_result(
                query=query,
                papers=papers,
                summaries=summaries,
                synthesis=synthesis_report,
                format_type=PresentationFormat.STRUCTURED_REPORT
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create result object
            result = ResearchResult(
                query=query,
                papers_found=papers,
                paper_summaries=summaries,
                synthesis_report=synthesis_report,
                formatted_report=formatted_report,
                presentation_format=PresentationFormat.STRUCTURED_REPORT,
                processing_time_seconds=processing_time,
                research_id=research_id,
                created_at=datetime.now()
            )
            
            # Store in database
            await self.database.store_research_result(result)
            
            # Update workflow state
            self.active_workflows[research_id]["status"] = "completed"
            self.active_workflows[research_id]["processing_time"] = processing_time
            
            logger.info(f"[{research_id}] Research workflow completed in {processing_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            # Handle workflow failure
            processing_time = time.time() - start_time
            
            self.active_workflows[research_id]["status"] = "failed"
            self.active_workflows[research_id]["error"] = str(e)
            self.active_workflows[research_id]["processing_time"] = processing_time
            
            logger.error(f"[{research_id}] Research workflow failed after {processing_time:.2f} seconds: {str(e)}")
            
            # Store failure in database
            await self.database.store_research_failure(research_id, query.query, str(e), processing_time)
            
            raise
        
        finally:
            # Cleanup workflow tracking after some time
            asyncio.create_task(self._cleanup_workflow_tracking(research_id, delay=300))  # 5 minutes
    
    async def get_workflow_status(self, research_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific research workflow"""
        return self.active_workflows.get(research_id)
    
    async def get_active_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get all active workflows"""
        return self.active_workflows.copy()
    
    async def get_research_history(self) -> List[ResearchHistoryEntry]:
        """Get history of previous research queries"""
        try:
            return await self.database.get_research_history()
        except Exception as e:
            logger.error(f"Failed to retrieve research history: {str(e)}")
            return []
    
    async def delete_research_entry(self, research_id: str):
        """Delete a specific research entry"""
        try:
            await self.database.delete_research_entry(research_id)
        except Exception as e:
            logger.error(f"Failed to delete research entry {research_id}: {str(e)}")
            raise
    
    async def get_research_result(self, research_id: str) -> Optional[ResearchResult]:
        """Retrieve a specific research result by ID"""
        try:
            return await self.database.get_research_result(research_id)
        except Exception as e:
            logger.error(f"Failed to retrieve research result {research_id}: {str(e)}")
            return None
    
    async def search_research_history(self, query_filter: str) -> List[ResearchHistoryEntry]:
        """Search research history by query content"""
        try:
            return await self.database.search_research_history(query_filter)
        except Exception as e:
            logger.error(f"Failed to search research history: {str(e)}")
            return []
    
    async def reformat_research_result(self, research_id: str, 
                                     new_format: PresentationFormat) -> Optional[str]:
        """Reformat an existing research result in a different presentation format"""
        try:
            # Retrieve existing result
            result = await self.get_research_result(research_id)
            if not result:
                return None
            
            # Reformat with new presentation format
            new_formatted_report = await self.presentation_agent.format_research_result(
                query=result.query,
                papers=result.papers_found,
                summaries=result.paper_summaries,
                synthesis=result.synthesis_report,
                format_type=new_format
            )
            
            # Update result in database
            await self.database.update_research_result_format(research_id, new_formatted_report, new_format)
            
            return new_formatted_report
            
        except Exception as e:
            logger.error(f"Failed to reformat research result {research_id}: {str(e)}")
            return None
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Get system usage statistics"""
        try:
            stats = await self.database.get_system_statistics()
            
            # Add current workflow information
            stats.update({
                "active_workflows": len(self.active_workflows),
                "workflow_details": {
                    wf_id: {
                        "status": details["status"],
                        "current_step": details.get("current_step"),
                        "elapsed_time": time.time() - details["start_time"]
                    }
                    for wf_id, details in self.active_workflows.items()
                }
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get system statistics: {str(e)}")
            return {
                "error": "Statistics not available",
                "active_workflows": len(self.active_workflows)
            }
    
    async def _cleanup_workflow_tracking(self, research_id: str, delay: int = 300):
        """Cleanup workflow tracking after delay"""
        await asyncio.sleep(delay)
        if research_id in self.active_workflows:
            del self.active_workflows[research_id]
            logger.debug(f"Cleaned up workflow tracking for {research_id}")
    
    async def _validate_research_query(self, query: ResearchQuery) -> bool:
        """Validate research query parameters"""
        if not query.query or len(query.query.strip()) < 3:
            raise ValueError("Query must be at least 3 characters long")
        
        if query.max_papers and (query.max_papers < 1 or query.max_papers > 50):
            raise ValueError("max_papers must be between 1 and 50")
        
        return True
    
    async def cancel_workflow(self, research_id: str) -> bool:
        """Cancel an active research workflow"""
        if research_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[research_id]
        if workflow["status"] != "in_progress":
            return False
        
        # Mark as cancelled
        workflow["status"] = "cancelled"
        workflow["cancelled_at"] = time.time()
        
        # Store cancellation in database
        processing_time = time.time() - workflow["start_time"]
        await self.database.store_research_failure(
            research_id, 
            "Unknown", 
            "Workflow cancelled by user", 
            processing_time
        )
        
        logger.info(f"Cancelled research workflow {research_id}")
        return True
    
    async def retry_failed_workflow(self, research_id: str) -> Optional[ResearchResult]:
        """Retry a failed research workflow"""
        try:
            # Get original query from database
            original_result = await self.database.get_research_result(research_id)
            if not original_result:
                return None
            
            # Execute workflow again with original query
            return await self.execute_research_workflow(original_result.query)
            
        except Exception as e:
            logger.error(f"Failed to retry workflow {research_id}: {str(e)}")
            return None
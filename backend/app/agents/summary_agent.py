"""
Summary Agent - Creates structured summaries of academic papers
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

# For production, you would use actual OpenAI API
# from openai import AsyncOpenAI

from ..models.schemas import Paper, PaperSummary

logger = logging.getLogger(__name__)

class SummaryAgent:
    """Agent responsible for summarizing individual academic papers"""
    
    def __init__(self):
        # In production, initialize with OpenAI API key
        # self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.summarization_prompts = {
            'objective': "Extract the main research objective or research question from this paper.",
            'methodology': "Describe the methodology or approach used in this research.",
            'findings': "List the key findings and results from this paper.",
            'conclusions': "Summarize the authors' main conclusions.",
            'limitations': "Identify any limitations mentioned by the authors."
        }
    
    async def initialize(self):
        """Initialize the summary agent"""
        logger.info("Initializing Summary Agent...")
        # Test AI service connection
        await self._test_ai_service()
        logger.info("Summary Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources"""
        pass
    
    async def summarize_paper(self, paper: Paper) -> PaperSummary:
        """
        Create a structured summary of an academic paper
        
        Args:
            paper: Paper object to summarize
            
        Returns:
            PaperSummary with structured summary components
        """
        logger.info(f"Summarizing paper: {paper.title[:50]}...")
        
        try:
            # Extract text content for summarization
            content = self._prepare_content_for_summarization(paper)
            
            # Generate structured summary components
            summary_components = await self._generate_summary_components(content)
            
            # Create summary object
            summary = PaperSummary(
                paper_id=paper.id,
                title=paper.title,
                authors=[author.name for author in paper.authors],
                objective=summary_components.get('objective', 'Objective not clearly identified'),
                methodology=summary_components.get('methodology', 'Methodology not clearly described'),
                key_findings=summary_components.get('key_findings', ['Key findings not identified']),
                conclusions=summary_components.get('conclusions', 'Conclusions not clearly stated'),
                limitations=summary_components.get('limitations'),
                summary_generated_at=datetime.now(),
                confidence_score=summary_components.get('confidence_score', 0.8)
            )
            
            logger.info(f"Successfully summarized paper: {paper.id}")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to summarize paper {paper.id}: {str(e)}")
            # Return a basic summary in case of failure
            return self._create_fallback_summary(paper)
    
    async def summarize_papers_batch(self, papers: List[Paper]) -> List[PaperSummary]:
        """
        Summarize multiple papers concurrently
        
        Args:
            papers: List of papers to summarize
            
        Returns:
            List of PaperSummary objects
        """
        logger.info(f"Batch summarizing {len(papers)} papers...")
        
        # Process papers concurrently with rate limiting
        semaphore = asyncio.Semaphore(3)  # Limit concurrent requests
        
        async def summarize_with_semaphore(paper):
            async with semaphore:
                return await self.summarize_paper(paper)
        
        tasks = [summarize_with_semaphore(paper) for paper in papers]
        summaries = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful summaries
        valid_summaries = [s for s in summaries if isinstance(s, PaperSummary)]
        
        logger.info(f"Successfully summarized {len(valid_summaries)}/{len(papers)} papers")
        return valid_summaries
    
    def _prepare_content_for_summarization(self, paper: Paper) -> str:
        """
        Prepare paper content for summarization by combining available text
        
        Args:
            paper: Paper object
            
        Returns:
            Combined text content for analysis
        """
        content_parts = []
        
        # Add title
        content_parts.append(f"Title: {paper.title}")
        
        # Add authors
        authors_text = ", ".join([author.name for author in paper.authors])
        content_parts.append(f"Authors: {authors_text}")
        
        # Add abstract (main content for summarization)
        if paper.abstract:
            content_parts.append(f"Abstract: {paper.abstract}")
        
        # Add keywords if available
        if paper.keywords:
            content_parts.append(f"Keywords: {', '.join(paper.keywords)}")
        
        return "\n\n".join(content_parts)
    
    async def _generate_summary_components(self, content: str) -> Dict[str, Any]:
        """
        Generate structured summary components using AI
        
        Args:
            content: Paper content to analyze
            
        Returns:
            Dictionary with summary components
        """
        # In production, this would use actual OpenAI API calls
        # For demo purposes, using rule-based extraction
        
        components = {}
        
        try:
            # Extract objective (simplified rule-based approach)
            components['objective'] = self._extract_objective(content)
            
            # Extract methodology
            components['methodology'] = self._extract_methodology(content)
            
            # Extract key findings
            components['key_findings'] = self._extract_key_findings(content)
            
            # Extract conclusions
            components['conclusions'] = self._extract_conclusions(content)
            
            # Extract limitations
            components['limitations'] = self._extract_limitations(content)
            
            # Set confidence score based on content quality
            components['confidence_score'] = self._calculate_confidence_score(content)
            
        except Exception as e:
            logger.error(f"Error generating summary components: {e}")
            components = self._get_default_components()
        
        return components
    
    def _extract_objective(self, content: str) -> str:
        """Extract research objective using pattern matching"""
        objective_patterns = [
            r'(?i)(?:objective|aim|goal|purpose)(?:s)?[\s\w]*?(?:is|are|was|were)?\s*(?:to\s+)?([^.]+)',
            r'(?i)(?:this\s+(?:study|research|paper|work))\s+(?:aims|seeks|attempts)\s+(?:to\s+)?([^.]+)',
            r'(?i)(?:we\s+(?:aim|seek|attempt|propose))\s+(?:to\s+)?([^.]+)',
        ]
        
        for pattern in objective_patterns:
            match = re.search(pattern, content)
            if match:
                objective = match.group(1).strip()
                if len(objective) > 20:  # Ensure it's substantial
                    return objective
        
        # Fallback: extract from first sentences of abstract
        abstract_match = re.search(r'Abstract:\s*([^.]+\.)', content)
        if abstract_match:
            return abstract_match.group(1).strip()
        
        return "Research objective not clearly identified in available text"
    
    def _extract_methodology(self, content: str) -> str:
        """Extract methodology using pattern matching"""
        method_patterns = [
            r'(?i)(?:method(?:ology)?|approach|technique)(?:s)?[\s\w]*?(?:used|employed|applied|adopted)[\s\w]*?([^.]+)',
            r'(?i)(?:we\s+(?:used|employed|applied|adopted|conducted))([^.]+)',
            r'(?i)(?:using|employing|applying)\s+([^.]+)',
        ]
        
        for pattern in method_patterns:
            match = re.search(pattern, content)
            if match:
                methodology = match.group(1).strip()
                if len(methodology) > 15:
                    return methodology
        
        return "Methodology not clearly described in available text"
    
    def _extract_key_findings(self, content: str) -> List[str]:
        """Extract key findings using pattern matching"""
        findings = []
        
        findings_patterns = [
            r'(?i)(?:result(?:s)?|finding(?:s)?|show(?:s|ed)?|demonstrate(?:s|d)?|reveal(?:s|ed)?)[\s\w]*?([^.]+)',
            r'(?i)(?:we\s+found|our\s+(?:results|findings)\s+(?:show|indicate|suggest))([^.]+)',
            r'(?i)(?:significantly|significantly\s+(?:higher|lower|different|improved))([^.]+)',
        ]
        
        for pattern in findings_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                finding = match.group(1).strip()
                if len(finding) > 20:
                    findings.append(finding)
        
        # Remove duplicates and limit to top 5
        unique_findings = list(dict.fromkeys(findings))[:5]
        
        if not unique_findings:
            unique_findings = ["Key findings not clearly identified in available text"]
        
        return unique_findings
    
    def _extract_conclusions(self, content: str) -> str:
        """Extract conclusions using pattern matching"""
        conclusion_patterns = [
            r'(?i)(?:conclusion(?:s)?|conclude|concluding)[\s\w]*?([^.]+)',
            r'(?i)(?:in\s+conclusion|to\s+conclude|we\s+conclude)([^.]+)',
            r'(?i)(?:these\s+(?:results|findings)\s+(?:suggest|indicate|show))([^.]+)',
        ]
        
        for pattern in conclusion_patterns:
            match = re.search(pattern, content)
            if match:
                conclusion = match.group(1).strip()
                if len(conclusion) > 20:
                    return conclusion
        
        return "Conclusions not clearly stated in available text"
    
    def _extract_limitations(self, content: str) -> Optional[str]:
        """Extract limitations using pattern matching"""
        limitation_patterns = [
            r'(?i)(?:limitation(?:s)?|limited\s+by|constraint(?:s)?)[\s\w]*?([^.]+)',
            r'(?i)(?:however|but|although|despite)[\s\w]*?(?:limitation(?:s)?)([^.]+)',
            r'(?i)(?:future\s+(?:work|research|studies)\s+(?:should|could|might))([^.]+)',
        ]
        
        for pattern in limitation_patterns:
            match = re.search(pattern, content)
            if match:
                limitation = match.group(1).strip()
                if len(limitation) > 15:
                    return limitation
        
        return None
    
    def _calculate_confidence_score(self, content: str) -> float:
        """Calculate confidence score based on content quality"""
        score = 0.5  # Base score
        
        # Increase score based on content richness
        if len(content) > 500:
            score += 0.2
        if len(content) > 1000:
            score += 0.1
        
        # Check for structured sections
        structured_terms = ['abstract', 'method', 'result', 'conclusion']
        found_terms = sum(1 for term in structured_terms if term.lower() in content.lower())
        score += found_terms * 0.05
        
        # Check for key research indicators
        research_indicators = ['study', 'analysis', 'experiment', 'data', 'hypothesis']
        found_indicators = sum(1 for indicator in research_indicators if indicator.lower() in content.lower())
        score += found_indicators * 0.02
        
        return min(score, 1.0)
    
    def _get_default_components(self) -> Dict[str, Any]:
        """Get default summary components in case of extraction failure"""
        return {
            'objective': 'Unable to extract research objective',
            'methodology': 'Unable to extract methodology',
            'key_findings': ['Unable to extract key findings'],
            'conclusions': 'Unable to extract conclusions',
            'limitations': None,
            'confidence_score': 0.3
        }
    
    def _create_fallback_summary(self, paper: Paper) -> PaperSummary:
        """Create a basic fallback summary when summarization fails"""
        return PaperSummary(
            paper_id=paper.id,
            title=paper.title,
            authors=[author.name for author in paper.authors],
            objective=f"Research objective analysis for: {paper.title}",
            methodology="Methodology information not available",
            key_findings=["Detailed analysis not available - please refer to original paper"],
            conclusions="Conclusions not available in current analysis",
            limitations=None,
            summary_generated_at=datetime.now(),
            confidence_score=0.2
        )
    
    async def _test_ai_service(self):
        """Test AI service connectivity"""
        # In production, this would test OpenAI API connection
        # For demo, just log that service is ready
        logger.info("AI summarization service ready (demo mode)")
        return True
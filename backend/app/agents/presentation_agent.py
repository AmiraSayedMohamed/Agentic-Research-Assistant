"""
Presentation Agent - Formats and presents research findings
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
import json

from ..models.schemas import (
    ResearchResult, Paper, PaperSummary, SynthesisReport, 
    PresentationFormat, ResearchQuery
)

logger = logging.getLogger(__name__)

class PresentationAgent:
    """Agent responsible for formatting and presenting research results"""
    
    def __init__(self):
        self.format_handlers = {
            PresentationFormat.STRUCTURED_REPORT: self._format_structured_report,
            PresentationFormat.EXECUTIVE_SUMMARY: self._format_executive_summary,
            PresentationFormat.BULLET_POINTS: self._format_bullet_points,
            PresentationFormat.ACADEMIC_PAPER: self._format_academic_paper,
        }
    
    async def initialize(self):
        """Initialize the presentation agent"""
        logger.info("Initializing Presentation Agent...")
        logger.info("Presentation Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources"""
        pass
    
    async def format_research_result(self, 
                                   query: ResearchQuery,
                                   papers: List[Paper],
                                   summaries: List[PaperSummary],
                                   synthesis: SynthesisReport,
                                   format_type: PresentationFormat = PresentationFormat.STRUCTURED_REPORT
                                   ) -> str:
        """
        Format research results into specified presentation format
        
        Args:
            query: Original research query
            papers: Found papers
            summaries: Paper summaries
            synthesis: Synthesis report
            format_type: Desired output format
            
        Returns:
            Formatted research report as string
        """
        logger.info(f"Formatting research results in {format_type} format")
        
        try:
            handler = self.format_handlers.get(format_type, self._format_structured_report)
            formatted_result = handler(query, papers, summaries, synthesis)
            
            logger.info("Research results formatted successfully")
            return formatted_result
            
        except Exception as e:
            logger.error(f"Failed to format research results: {str(e)}")
            return self._format_fallback_report(query, papers, summaries, synthesis)
    
    def _format_structured_report(self, 
                                query: ResearchQuery,
                                papers: List[Paper],
                                summaries: List[PaperSummary],
                                synthesis: SynthesisReport) -> str:
        """Format as structured research report"""
        
        report_sections = []
        
        # Header
        report_sections.append("# Research Analysis Report")
        report_sections.append(f"**Query:** {query.query}")
        report_sections.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append(f"**Papers analyzed:** {len(papers)}")
        report_sections.append("")
        
        # Executive Summary
        report_sections.append("## Executive Summary")
        report_sections.append(synthesis.executive_summary)
        report_sections.append("")
        
        # Key Findings
        report_sections.append("## Key Findings")
        if synthesis.consensus_findings:
            report_sections.append("### Consensus Findings")
            for finding in synthesis.consensus_findings:
                report_sections.append(f"- {finding}")
        
        if synthesis.conflicting_results:
            report_sections.append("### Conflicting Results")
            for conflict in synthesis.conflicting_results:
                report_sections.append(f"- {conflict}")
        report_sections.append("")
        
        # Main Themes
        if synthesis.main_themes:
            report_sections.append("## Main Themes")
            for theme in synthesis.main_themes:
                report_sections.append(f"### {theme.theme}")
                report_sections.append(f"**Evidence Strength:** {theme.evidence_strength.title()}")
                report_sections.append(f"**Description:** {theme.description}")
                report_sections.append(f"**Supporting Papers:** {len(theme.supporting_papers)}")
                report_sections.append("")
        
        # Methodology Analysis
        report_sections.append("## Methodology Analysis")
        report_sections.append(synthesis.methodology_analysis)
        report_sections.append("")
        
        # Research Gaps
        if synthesis.research_gaps:
            report_sections.append("## Identified Research Gaps")
            for gap in synthesis.research_gaps:
                report_sections.append(f"### {gap.gap_description}")
                report_sections.append(f"**Potential Impact:** {gap.potential_impact.title()}")
                if gap.suggested_research_directions:
                    report_sections.append("**Suggested Research Directions:**")
                    for direction in gap.suggested_research_directions:
                        report_sections.append(f"- {direction}")
                report_sections.append("")
        
        # Individual Paper Summaries
        report_sections.append("## Individual Paper Summaries")
        for i, summary in enumerate(summaries, 1):
            report_sections.append(f"### Paper {i}: {summary.title}")
            report_sections.append(f"**Authors:** {', '.join(summary.authors)}")
            report_sections.append(f"**Objective:** {summary.objective}")
            report_sections.append(f"**Methodology:** {summary.methodology}")
            
            report_sections.append("**Key Findings:**")
            for finding in summary.key_findings:
                report_sections.append(f"- {finding}")
            
            report_sections.append(f"**Conclusions:** {summary.conclusions}")
            
            if summary.limitations:
                report_sections.append(f"**Limitations:** {summary.limitations}")
            
            report_sections.append("")
        
        # References
        report_sections.append("## References")
        for i, paper in enumerate(papers, 1):
            authors_str = ", ".join([author.name for author in paper.authors])
            report_sections.append(f"{i}. {authors_str}. {paper.title}. {paper.source.value.title()}. {paper.published_date.year}. {paper.url}")
        
        return "\n".join(report_sections)
    
    def _format_executive_summary(self,
                                query: ResearchQuery,
                                papers: List[Paper],
                                summaries: List[PaperSummary],
                                synthesis: SynthesisReport) -> str:
        """Format as executive summary"""
        
        summary_sections = []
        
        # Header
        summary_sections.append("# Executive Summary")
        summary_sections.append(f"**Research Query:** {query.query}")
        summary_sections.append(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}")
        summary_sections.append("")
        
        # Overview
        summary_sections.append("## Overview")
        summary_sections.append(synthesis.executive_summary)
        summary_sections.append("")
        
        # Key Insights (top 3)
        summary_sections.append("## Key Insights")
        insights_count = 0
        
        if synthesis.consensus_findings and insights_count < 3:
            for finding in synthesis.consensus_findings[:3-insights_count]:
                summary_sections.append(f"• {finding}")
                insights_count += 1
        
        if synthesis.main_themes and insights_count < 3:
            remaining = 3 - insights_count
            for theme in synthesis.main_themes[:remaining]:
                summary_sections.append(f"• {theme.description}")
                insights_count += 1
        
        summary_sections.append("")
        
        # Recommendations
        summary_sections.append("## Recommendations")
        if synthesis.research_gaps:
            gap = synthesis.research_gaps[0]  # Top gap
            if gap.suggested_research_directions:
                for direction in gap.suggested_research_directions[:2]:
                    summary_sections.append(f"• {direction}")
        else:
            summary_sections.append("• Continue monitoring developments in this research area")
            summary_sections.append("• Consider conducting follow-up analysis with additional papers")
        
        summary_sections.append("")
        
        # Statistics
        summary_sections.append("## Analysis Statistics")
        summary_sections.append(f"• Papers Analyzed: {len(papers)}")
        summary_sections.append(f"• Main Themes Identified: {len(synthesis.main_themes)}")
        summary_sections.append(f"• Consensus Areas: {len(synthesis.consensus_findings)}")
        summary_sections.append(f"• Research Gaps: {len(synthesis.research_gaps)}")
        
        return "\n".join(summary_sections)
    
    def _format_bullet_points(self,
                            query: ResearchQuery,
                            papers: List[Paper],
                            summaries: List[PaperSummary],
                            synthesis: SynthesisReport) -> str:
        """Format as bullet-point summary"""
        
        bullet_sections = []
        
        # Header
        bullet_sections.append(f"# Research Summary: {query.query}")
        bullet_sections.append("")
        
        # Quick Stats
        bullet_sections.append("## Quick Overview")
        bullet_sections.append(f"• Query: {query.query}")
        bullet_sections.append(f"• Papers analyzed: {len(papers)}")
        bullet_sections.append(f"• Analysis date: {datetime.now().strftime('%Y-%m-%d')}")
        bullet_sections.append("")
        
        # Key Findings
        bullet_sections.append("## Key Findings")
        if synthesis.consensus_findings:
            for finding in synthesis.consensus_findings:
                bullet_sections.append(f"• {finding}")
        
        if synthesis.main_themes:
            bullet_sections.append(f"• Main research themes: {', '.join([theme.theme for theme in synthesis.main_themes[:3]])}")
        
        bullet_sections.append("")
        
        # Top Papers
        bullet_sections.append("## Top Papers")
        for i, (paper, summary) in enumerate(zip(papers[:3], summaries[:3]), 1):
            authors = ", ".join([author.name for author in paper.authors[:2]])
            if len(paper.authors) > 2:
                authors += " et al."
            bullet_sections.append(f"• **Paper {i}:** {paper.title}")
            bullet_sections.append(f"  - Authors: {authors}")
            bullet_sections.append(f"  - Key finding: {summary.key_findings[0] if summary.key_findings else 'Not specified'}")
        
        bullet_sections.append("")
        
        # Research Gaps
        if synthesis.research_gaps:
            bullet_sections.append("## Research Opportunities")
            for gap in synthesis.research_gaps[:2]:
                bullet_sections.append(f"• {gap.gap_description}")
        
        return "\n".join(bullet_sections)
    
    def _format_academic_paper(self,
                             query: ResearchQuery,
                             papers: List[Paper],
                             summaries: List[PaperSummary],
                             synthesis: SynthesisReport) -> str:
        """Format as academic paper structure"""
        
        paper_sections = []
        
        # Title and Abstract
        paper_sections.append(f"# A Systematic Review of Research on: {query.query}")
        paper_sections.append("")
        paper_sections.append("## Abstract")
        paper_sections.append(f"This systematic review analyzes {len(papers)} papers related to '{query.query}'. ")
        paper_sections.append(synthesis.executive_summary)
        paper_sections.append("")
        
        # Introduction
        paper_sections.append("## Introduction")
        paper_sections.append(f"The field of research surrounding '{query.query}' has generated significant scholarly interest. ")
        paper_sections.append(f"This review synthesizes findings from {len(papers)} recent publications to provide ")
        paper_sections.append("a comprehensive understanding of the current state of knowledge.")
        paper_sections.append("")
        
        # Methods
        paper_sections.append("## Methods")
        paper_sections.append("### Literature Search Strategy")
        paper_sections.append(f"Papers were identified using the search query: '{query.query}'. ")
        paper_sections.append(f"A total of {len(papers)} papers were retrieved and analyzed.")
        paper_sections.append("")
        paper_sections.append("### Analysis Approach")
        paper_sections.append(synthesis.methodology_analysis)
        paper_sections.append("")
        
        # Results
        paper_sections.append("## Results")
        
        if synthesis.main_themes:
            paper_sections.append("### Thematic Analysis")
            paper_sections.append(f"The analysis revealed {len(synthesis.main_themes)} main themes:")
            for theme in synthesis.main_themes:
                paper_sections.append(f"**{theme.theme}** ({theme.evidence_strength} evidence): {theme.description}")
            paper_sections.append("")
        
        if synthesis.consensus_findings:
            paper_sections.append("### Consensus Findings")
            paper_sections.append("Several areas of consensus emerged from the literature:")
            for finding in synthesis.consensus_findings:
                paper_sections.append(f"- {finding}")
            paper_sections.append("")
        
        if synthesis.conflicting_results:
            paper_sections.append("### Areas of Disagreement")
            paper_sections.append("The following conflicting results were identified:")
            for conflict in synthesis.conflicting_results:
                paper_sections.append(f"- {conflict}")
            paper_sections.append("")
        
        # Discussion
        paper_sections.append("## Discussion")
        paper_sections.append("### Implications")
        paper_sections.append("The findings from this review have several important implications for the field.")
        if synthesis.consensus_findings:
            paper_sections.append(f"The consensus around {synthesis.consensus_findings[0].lower()} suggests ")
            paper_sections.append("that this area has reached a level of maturity warranting practical application.")
        paper_sections.append("")
        
        # Limitations and Future Work
        paper_sections.append("### Limitations and Future Research")
        if synthesis.research_gaps:
            paper_sections.append("Several research gaps were identified:")
            for gap in synthesis.research_gaps:
                paper_sections.append(f"**{gap.gap_description}** (Impact: {gap.potential_impact})")
                if gap.suggested_research_directions:
                    paper_sections.append("Future research should consider:")
                    for direction in gap.suggested_research_directions:
                        paper_sections.append(f"- {direction}")
        paper_sections.append("")
        
        # Conclusion
        paper_sections.append("## Conclusion")
        paper_sections.append(f"This review of {len(papers)} papers provides a comprehensive overview of ")
        paper_sections.append(f"research on '{query.query}'. The analysis reveals both areas of consensus ")
        paper_sections.append("and opportunities for future investigation.")
        paper_sections.append("")
        
        # References (simplified)
        paper_sections.append("## References")
        for i, paper in enumerate(papers, 1):
            authors_str = ", ".join([author.name for author in paper.authors[:3]])
            if len(paper.authors) > 3:
                authors_str += " et al."
            paper_sections.append(f"[{i}] {authors_str} ({paper.published_date.year}). {paper.title}. ")
            paper_sections.append(f"    Retrieved from {paper.url}")
        
        return "\n".join(paper_sections)
    
    def _format_fallback_report(self,
                              query: ResearchQuery,
                              papers: List[Paper],
                              summaries: List[PaperSummary],
                              synthesis: SynthesisReport) -> str:
        """Create fallback report when formatting fails"""
        
        fallback_sections = []
        
        fallback_sections.append("# Research Analysis Report")
        fallback_sections.append(f"Query: {query.query}")
        fallback_sections.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        fallback_sections.append("")
        
        fallback_sections.append("## Summary")
        fallback_sections.append(f"Analyzed {len(papers)} papers related to your query.")
        fallback_sections.append("Detailed formatting not available - please try again.")
        fallback_sections.append("")
        
        if papers:
            fallback_sections.append("## Papers Found")
            for i, paper in enumerate(papers[:5], 1):
                fallback_sections.append(f"{i}. {paper.title}")
                fallback_sections.append(f"   Authors: {', '.join([author.name for author in paper.authors[:2]])}")
                fallback_sections.append(f"   URL: {paper.url}")
                fallback_sections.append("")
        
        return "\n".join(fallback_sections)
    
    def export_to_json(self, research_result: ResearchResult) -> str:
        """Export research result to JSON format"""
        try:
            # Convert to JSON-serializable format
            result_dict = {
                "query": research_result.query.dict(),
                "papers_found": [paper.dict() for paper in research_result.papers_found],
                "paper_summaries": [summary.dict() for summary in research_result.paper_summaries],
                "synthesis_report": research_result.synthesis_report.dict(),
                "formatted_report": research_result.formatted_report,
                "presentation_format": research_result.presentation_format.value,
                "metadata": {
                    "processing_time_seconds": research_result.processing_time_seconds,
                    "total_tokens_used": research_result.total_tokens_used,
                    "research_id": research_result.research_id,
                    "created_at": research_result.created_at.isoformat()
                }
            }
            
            return json.dumps(result_dict, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Failed to export to JSON: {str(e)}")
            return json.dumps({"error": "Export failed", "message": str(e)}, indent=2)
    
    def export_citations(self, papers: List[Paper], format_style: str = "APA") -> str:
        """Export paper citations in specified format"""
        citations = []
        
        for paper in papers:
            if format_style.upper() == "APA":
                citation = self._format_apa_citation(paper)
            elif format_style.upper() == "MLA":
                citation = self._format_mla_citation(paper)
            else:
                citation = self._format_basic_citation(paper)
            
            citations.append(citation)
        
        return "\n".join(citations)
    
    def _format_apa_citation(self, paper: Paper) -> str:
        """Format paper citation in APA style"""
        authors = paper.authors[:3]  # APA typically shows first 3 authors
        
        if len(authors) == 1:
            author_str = f"{authors[0].name}"
        elif len(authors) == 2:
            author_str = f"{authors[0].name} & {authors[1].name}"
        else:
            author_str = f"{authors[0].name}, {authors[1].name}, & {authors[2].name}"
        
        if len(paper.authors) > 3:
            author_str += " et al."
        
        year = paper.published_date.year
        title = paper.title
        
        return f"{author_str} ({year}). {title}. Retrieved from {paper.url}"
    
    def _format_mla_citation(self, paper: Paper) -> str:
        """Format paper citation in MLA style"""
        if paper.authors:
            author_str = paper.authors[0].name
            if len(paper.authors) > 1:
                author_str += " et al."
        else:
            author_str = "Unknown Author"
        
        title = f'"{paper.title}"'
        year = paper.published_date.year
        
        return f'{author_str}. {title} {year}. Web. {datetime.now().strftime("%d %b %Y")}.'
    
    def _format_basic_citation(self, paper: Paper) -> str:
        """Format basic citation"""
        authors_str = ", ".join([author.name for author in paper.authors[:2]])
        if len(paper.authors) > 2:
            authors_str += " et al."
        
        return f"{authors_str}. {paper.title}. {paper.published_date.year}. {paper.url}"
"""
Synthesis Agent - Synthesizes findings across multiple papers
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from collections import Counter, defaultdict
import re

from ..models.schemas import PaperSummary, SynthesisReport, SynthesisTheme, ResearchGap

logger = logging.getLogger(__name__)

class SynthesisAgent:
    """Agent responsible for synthesizing information across multiple research papers"""
    
    def __init__(self):
        self.theme_keywords = {
            'methodology': ['method', 'approach', 'technique', 'algorithm', 'framework'],
            'performance': ['performance', 'accuracy', 'efficiency', 'speed', 'optimization'],
            'results': ['result', 'finding', 'outcome', 'conclusion', 'evidence'],
            'limitations': ['limitation', 'constraint', 'challenge', 'issue', 'problem'],
            'future_work': ['future', 'further', 'next', 'upcoming', 'potential']
        }
    
    async def initialize(self):
        """Initialize the synthesis agent"""
        logger.info("Initializing Synthesis Agent...")
        logger.info("Synthesis Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources"""
        pass
    
    async def synthesize_papers(self, summaries: List[PaperSummary], query: str) -> SynthesisReport:
        """
        Synthesize findings across multiple paper summaries
        
        Args:
            summaries: List of paper summaries to synthesize
            query: Original research query for context
            
        Returns:
            SynthesisReport with cross-paper analysis
        """
        logger.info(f"Synthesizing {len(summaries)} paper summaries for query: '{query}'")
        
        try:
            # Extract themes and patterns
            main_themes = await self._identify_themes(summaries)
            
            # Find consensus and conflicts
            consensus_findings = self._find_consensus(summaries)
            conflicting_results = self._find_conflicts(summaries)
            
            # Identify research gaps
            research_gaps = self._identify_research_gaps(summaries, query)
            
            # Analyze methodologies
            methodology_analysis = self._analyze_methodologies(summaries)
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                summaries, main_themes, consensus_findings, query
            )
            
            # Calculate synthesis confidence
            synthesis_confidence = self._calculate_synthesis_confidence(summaries)
            
            report = SynthesisReport(
                query=query,
                paper_ids=[s.paper_id for s in summaries],
                total_papers=len(summaries),
                executive_summary=executive_summary,
                main_themes=main_themes,
                consensus_findings=consensus_findings,
                conflicting_results=conflicting_results,
                research_gaps=research_gaps,
                methodology_analysis=methodology_analysis,
                generated_at=datetime.now(),
                synthesis_confidence=synthesis_confidence
            )
            
            logger.info(f"Successfully synthesized {len(summaries)} papers")
            return report
            
        except Exception as e:
            logger.error(f"Failed to synthesize papers: {str(e)}")
            return self._create_fallback_synthesis(summaries, query)
    
    async def _identify_themes(self, summaries: List[PaperSummary]) -> List[SynthesisTheme]:
        """Identify main themes across paper summaries"""
        theme_occurrences = defaultdict(list)
        theme_descriptions = {}
        
        # Analyze each summary for themes
        for summary in summaries:
            # Combine text for analysis
            text = f"{summary.objective} {summary.methodology} {' '.join(summary.key_findings)} {summary.conclusions}"
            text_lower = text.lower()
            
            # Check for theme keywords
            for theme_name, keywords in self.theme_keywords.items():
                keyword_matches = sum(1 for keyword in keywords if keyword in text_lower)
                if keyword_matches > 0:
                    theme_occurrences[theme_name].append(summary.paper_id)
                    
                    # Generate theme description
                    if theme_name not in theme_descriptions:
                        theme_descriptions[theme_name] = self._generate_theme_description(theme_name, keywords)
        
        # Create SynthesisTheme objects
        themes = []
        for theme_name, paper_ids in theme_occurrences.items():
            if len(paper_ids) >= 2:  # Theme must appear in at least 2 papers
                evidence_strength = self._calculate_evidence_strength(len(paper_ids), len(summaries))
                
                theme = SynthesisTheme(
                    theme=theme_name.replace('_', ' ').title(),
                    description=theme_descriptions.get(theme_name, f"Analysis of {theme_name} across papers"),
                    supporting_papers=paper_ids,
                    evidence_strength=evidence_strength
                )
                themes.append(theme)
        
        # Sort themes by strength and number of supporting papers
        themes.sort(key=lambda x: (len(x.supporting_papers), x.evidence_strength), reverse=True)
        
        return themes[:10]  # Return top 10 themes
    
    def _find_consensus(self, summaries: List[PaperSummary]) -> List[str]:
        """Find consensus findings across papers"""
        consensus_findings = []
        
        # Extract key terms from findings
        all_findings = []
        for summary in summaries:
            all_findings.extend([finding.lower() for finding in summary.key_findings])
        
        # Find common patterns
        finding_words = []
        for finding in all_findings:
            # Extract significant words (excluding common words)
            words = re.findall(r'\b[a-zA-Z]{4,}\b', finding)
            finding_words.extend(words)
        
        # Count word frequencies
        word_counts = Counter(finding_words)
        common_words = [word for word, count in word_counts.most_common(20) if count >= 2]
        
        # Generate consensus statements
        if common_words:
            consensus_patterns = self._identify_consensus_patterns(summaries, common_words)
            consensus_findings.extend(consensus_patterns)
        
        # Add methodology consensus if found
        methodology_consensus = self._find_methodology_consensus(summaries)
        if methodology_consensus:
            consensus_findings.append(f"Methodology consensus: {methodology_consensus}")
        
        return consensus_findings[:5]  # Return top 5 consensus findings
    
    def _find_conflicts(self, summaries: List[PaperSummary]) -> List[str]:
        """Identify conflicting results across papers"""
        conflicts = []
        
        # Look for contradictory terms in findings
        conflict_indicators = [
            ('increased', 'decreased'),
            ('improved', 'worsened'),
            ('significant', 'insignificant'),
            ('effective', 'ineffective'),
            ('higher', 'lower'),
            ('positive', 'negative')
        ]
        
        for summary1 in summaries:
            for summary2 in summaries[summaries.index(summary1)+1:]:
                conflict = self._detect_conflict_between_papers(summary1, summary2, conflict_indicators)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts[:3]  # Return top 3 conflicts
    
    def _identify_research_gaps(self, summaries: List[PaperSummary], query: str) -> List[ResearchGap]:
        """Identify potential research gaps"""
        gaps = []
        
        # Analyze limitations across papers
        all_limitations = [s.limitations for s in summaries if s.limitations]
        
        if all_limitations:
            # Common limitation themes
            limitation_themes = self._extract_limitation_themes(all_limitations)
            
            for theme in limitation_themes:
                gap = ResearchGap(
                    gap_description=f"Limited research on {theme}",
                    related_themes=[theme],
                    potential_impact="medium",
                    suggested_research_directions=[
                        f"Investigate {theme} in more detail",
                        f"Develop new methods to address {theme}",
                        f"Conduct longitudinal studies on {theme}"
                    ]
                )
                gaps.append(gap)
        
        # Identify methodological gaps
        methodologies = [s.methodology for s in summaries]
        method_diversity = len(set(methodologies))
        
        if method_diversity < len(summaries) * 0.7:  # Low methodological diversity
            gaps.append(ResearchGap(
                gap_description="Limited methodological diversity in current research",
                related_themes=["methodology"],
                potential_impact="high",
                suggested_research_directions=[
                    "Explore alternative research methodologies",
                    "Combine multiple methodological approaches",
                    "Develop novel analytical frameworks"
                ]
            ))
        
        return gaps[:5]  # Return top 5 gaps
    
    def _analyze_methodologies(self, summaries: List[PaperSummary]) -> str:
        """Analyze methodologies used across papers"""
        methodologies = [s.methodology for s in summaries]
        method_counter = Counter(methodologies)
        
        analysis_parts = []
        
        # Most common methodology
        if method_counter:
            most_common = method_counter.most_common(1)[0]
            analysis_parts.append(f"Most frequently used approach: {most_common[0]} (used in {most_common[1]} papers)")
        
        # Methodology diversity
        unique_methods = len(set(methodologies))
        diversity_ratio = unique_methods / len(methodologies) if methodologies else 0
        
        if diversity_ratio > 0.8:
            analysis_parts.append("High methodological diversity observed across studies")
        elif diversity_ratio < 0.3:
            analysis_parts.append("Limited methodological diversity - most studies use similar approaches")
        else:
            analysis_parts.append("Moderate methodological diversity across studies")
        
        # Identify method categories
        method_categories = self._categorize_methodologies(methodologies)
        if method_categories:
            analysis_parts.append(f"Primary methodological categories: {', '.join(method_categories)}")
        
        return ". ".join(analysis_parts)
    
    def _generate_executive_summary(self, summaries: List[PaperSummary], themes: List[SynthesisTheme], 
                                  consensus: List[str], query: str) -> str:
        """Generate executive summary of the synthesis"""
        summary_parts = []
        
        # Introduction
        summary_parts.append(f"Analysis of {len(summaries)} papers related to '{query}' reveals several key insights.")
        
        # Main themes
        if themes:
            theme_names = [theme.theme for theme in themes[:3]]
            summary_parts.append(f"The primary research themes include: {', '.join(theme_names)}.")
        
        # Consensus findings
        if consensus:
            summary_parts.append(f"There is consensus across studies regarding: {consensus[0]}")
        
        # Research maturity assessment
        avg_confidence = sum(s.confidence_score or 0.5 for s in summaries) / len(summaries)
        if avg_confidence > 0.8:
            summary_parts.append("The research field demonstrates high confidence and mature findings.")
        elif avg_confidence < 0.5:
            summary_parts.append("The research field shows emerging findings that require further validation.")
        else:
            summary_parts.append("The research field shows moderate confidence with established patterns.")
        
        return " ".join(summary_parts)
    
    def _calculate_synthesis_confidence(self, summaries: List[PaperSummary]) -> float:
        """Calculate confidence score for the synthesis"""
        if not summaries:
            return 0.0
        
        # Base confidence on individual paper confidence scores
        individual_confidences = [s.confidence_score or 0.5 for s in summaries]
        avg_confidence = sum(individual_confidences) / len(individual_confidences)
        
        # Adjust based on number of papers
        size_factor = min(1.0, len(summaries) / 10)  # More papers = higher confidence
        
        # Adjust based on consistency (simplified)
        consistency_factor = 0.9 if len(summaries) > 1 else 0.7
        
        final_confidence = avg_confidence * size_factor * consistency_factor
        return min(final_confidence, 1.0)
    
    def _generate_theme_description(self, theme_name: str, keywords: List[str]) -> str:
        """Generate description for a theme"""
        descriptions = {
            'methodology': "Analysis of research methods and approaches used across studies",
            'performance': "Examination of performance metrics and efficiency measures",
            'results': "Synthesis of key findings and outcomes reported in studies",
            'limitations': "Common limitations and constraints identified across research",
            'future_work': "Suggested directions for future research and development"
        }
        return descriptions.get(theme_name, f"Analysis of {theme_name} patterns across studies")
    
    def _calculate_evidence_strength(self, supporting_papers: int, total_papers: int) -> str:
        """Calculate evidence strength based on paper support"""
        ratio = supporting_papers / total_papers
        if ratio >= 0.7:
            return "strong"
        elif ratio >= 0.4:
            return "moderate"
        else:
            return "weak"
    
    def _identify_consensus_patterns(self, summaries: List[PaperSummary], common_words: List[str]) -> List[str]:
        """Identify consensus patterns from common words"""
        patterns = []
        
        # Simple pattern detection based on common words
        if 'effective' in common_words or 'successful' in common_words:
            patterns.append("Multiple studies report effectiveness of the investigated approaches")
        
        if 'significant' in common_words:
            patterns.append("Significant results are consistently reported across studies")
        
        if 'improved' in common_words or 'improvement' in common_words:
            patterns.append("Consistent improvements are observed across different implementations")
        
        return patterns
    
    def _find_methodology_consensus(self, summaries: List[PaperSummary]) -> Optional[str]:
        """Find consensus in methodological approaches"""
        methodologies = [s.methodology.lower() for s in summaries]
        
        # Look for common methodological terms
        common_terms = ['experimental', 'survey', 'analysis', 'comparison', 'evaluation']
        term_counts = {term: sum(1 for method in methodologies if term in method) for term in common_terms}
        
        dominant_term = max(term_counts, key=term_counts.get)
        if term_counts[dominant_term] >= len(summaries) * 0.6:
            return f"Most studies employ {dominant_term} approaches"
        
        return None
    
    def _detect_conflict_between_papers(self, summary1: PaperSummary, summary2: PaperSummary, 
                                      conflict_indicators: List[tuple]) -> Optional[str]:
        """Detect conflicts between two papers"""
        text1 = " ".join(summary1.key_findings).lower()
        text2 = " ".join(summary2.key_findings).lower()
        
        for positive, negative in conflict_indicators:
            if positive in text1 and negative in text2:
                return f"Conflicting findings: {summary1.title} reports {positive} results while {summary2.title} reports {negative} results"
            elif negative in text1 and positive in text2:
                return f"Conflicting findings: {summary1.title} reports {negative} results while {summary2.title} reports {positive} results"
        
        return None
    
    def _extract_limitation_themes(self, limitations: List[str]) -> List[str]:
        """Extract common themes from limitations"""
        all_text = " ".join(limitations).lower()
        
        limitation_themes = []
        theme_keywords = {
            'sample size': ['sample', 'size', 'participants'],
            'data quality': ['data', 'quality', 'accuracy'],
            'generalizability': ['generalizability', 'external', 'validity'],
            'methodology': ['method', 'approach', 'design'],
            'time constraints': ['time', 'duration', 'longitudinal']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                limitation_themes.append(theme)
        
        return limitation_themes
    
    def _categorize_methodologies(self, methodologies: List[str]) -> List[str]:
        """Categorize methodologies into broad categories"""
        categories = []
        all_text = " ".join(methodologies).lower()
        
        category_keywords = {
            'Experimental': ['experiment', 'trial', 'test'],
            'Analytical': ['analysis', 'statistical', 'mathematical'],
            'Computational': ['computational', 'simulation', 'model'],
            'Observational': ['observational', 'survey', 'study']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                categories.append(category)
        
        return categories
    
    def _create_fallback_synthesis(self, summaries: List[PaperSummary], query: str) -> SynthesisReport:
        """Create fallback synthesis report in case of error"""
        return SynthesisReport(
            query=query,
            paper_ids=[s.paper_id for s in summaries],
            total_papers=len(summaries),
            executive_summary=f"Analysis of {len(summaries)} papers related to '{query}'. Detailed synthesis not available.",
            main_themes=[],
            consensus_findings=["Synthesis analysis not available"],
            conflicting_results=[],
            research_gaps=[],
            methodology_analysis="Methodology analysis not available",
            generated_at=datetime.now(),
            synthesis_confidence=0.3
        )
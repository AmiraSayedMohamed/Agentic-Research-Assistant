"""Agents package for multi-agent research system"""

from .research_agent import ResearchAgent
from .summary_agent import SummaryAgent
from .synthesis_agent import SynthesisAgent
from .presentation_agent import PresentationAgent

__all__ = [
    "ResearchAgent",
    "SummaryAgent",
    "SynthesisAgent", 
    "PresentationAgent"
]
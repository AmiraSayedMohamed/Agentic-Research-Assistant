import asyncio
import logging
from typing import List, Dict, Any
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SynthesizerAgent:
    """Advanced synthesis agent for generating comprehensive research reports"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.studio.nebius.ai/v1"
        self.model = "meta-llama/Meta-Llama-3.1-70B-Instruct"
        self.session: aiohttp.ClientSession = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def synthesize_report(self, summaries: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Generate comprehensive synthesized report from paper summaries"""
        logger.info(f"Synthesizing report from {len(summaries)} summaries for query: {query}")
        
        try:
            # Generate different sections of the report
            synthesis_tasks = [
                self._generate_executive_summary(summaries, query),
                self._identify_themes(summaries, query),
                self._analyze_gaps_and_limitations(summaries, query),
                self._generate_recommendations(summaries, query)
            ]
            
            results = await asyncio.gather(*synthesis_tasks)
            
            executive_summary = results[0]
            themes = results[1]
            gaps_analysis = results[2]
            recommendations = results[3]
            
            # Generate full report text
            full_report = await self._generate_full_report(
                executive_summary, themes, gaps_analysis, recommendations, summaries, query
            )
            
            # Create citations list
            citations = self._create_citations(summaries)
            
            return {
                'executive_summary': executive_summary,
                'themes': themes,
                'gaps': gaps_analysis['gaps'],
                'limitations': gaps_analysis['limitations'],
                'recommendations': recommendations,
                'citations': citations,
                'full_text': full_report,
                'metadata': {
                    'query': query,
                    'papers_analyzed': len(summaries),
                    'generated_at': datetime.now().isoformat(),
                    'word_count': len(full_report.split())
                }
            }
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return self._create_fallback_report(summaries, query)
    
    async def _generate_executive_summary(self, summaries: List[Dict[str, Any]], query: str) -> str:
        """Generate executive summary of the research landscape"""
        prompt = f"""
You are an expert research analyst. Create a comprehensive executive summary based on the following research papers related to "{query}".

PAPER SUMMARIES:
{self._format_summaries_for_prompt(summaries)}

Generate a 150-200 word executive summary that:
1. Provides an overview of the current research landscape for "{query}"
2. Highlights the most significant findings across papers
3. Identifies the overall state of knowledge in this field
4. Mentions the number of papers analyzed ({len(summaries)} papers)

Write in a professional, academic tone. Focus on synthesis rather than listing individual papers.
"""
        
        response = await self._call_nebius_api(prompt)
        return self._extract_text_response(response)
    
    async def _identify_themes(self, summaries: List[Dict[str, Any]], query: str) -> List[Dict[str, str]]:
        """Identify major themes across the research papers"""
        prompt = f"""
Analyze the following research papers about "{query}" and identify 3-5 major themes that emerge across the literature.

PAPER SUMMARIES:
{self._format_summaries_for_prompt(summaries)}

For each theme, provide:
1. A clear theme name (2-4 words)
2. A detailed description (50-80 words) explaining the theme
3. Which papers contribute to this theme (use paper titles)

Return your response as a JSON array:
[
    {{
        "name": "Theme Name",
        "description": "Detailed description of the theme and its significance",
        "contributing_papers": ["Paper Title 1", "Paper Title 2"]
    }}
]

Focus on themes that appear across multiple papers, not isolated findings.
"""
        
        response = await self._call_nebius_api(prompt)
        return self._parse_json_response(response, [])
    
    async def _analyze_gaps_and_limitations(self, summaries: List[Dict[str, Any]], query: str) -> Dict[str, List]:
        """Identify research gaps and limitations"""
        prompt = f"""
Analyze the research papers about "{query}" and identify:
1. Research gaps (areas not adequately covered)
2. Methodological limitations across studies
3. Opportunities for future research

PAPER SUMMARIES:
{self._format_summaries_for_prompt(summaries)}

Return a JSON object:
{{
    "gaps": [
        {{
            "description": "Clear description of the research gap",
            "evidence": "Specific evidence from papers (cite paper titles)",
            "priority": "High|Medium|Low",
            "supporting_citations": ["Paper titles that support this gap identification"]
        }}
    ],
    "limitations": [
        {{
            "description": "Methodological or conceptual limitation",
            "affected_papers": ["Paper titles with this limitation"],
            "impact": "Description of how this limitation affects findings"
        }}
    ]
}}

Focus on gaps that represent genuine opportunities for advancing the field.
"""
        
        response = await self._call_nebius_api(prompt)
        return self._parse_json_response(response, {"gaps": [], "limitations": []})
    
    async def _generate_recommendations(self, summaries: List[Dict[str, Any]], query: str) -> List[str]:
        """Generate actionable recommendations based on the research"""
        prompt = f"""
Based on the research papers about "{query}", generate 4-6 specific, actionable recommendations for:
1. Future research directions
2. Methodological improvements
3. Practical applications
4. Policy or implementation considerations

PAPER SUMMARIES:
{self._format_summaries_for_prompt(summaries)}

Return a JSON array of recommendation strings:
[
    "Specific recommendation 1 with clear action items",
    "Specific recommendation 2 addressing identified gaps",
    ...
]

Each recommendation should be:
- Specific and actionable
- Based on evidence from the papers
- Relevant to advancing the field of "{query}"
- 15-25 words long
"""
        
        response = await self._call_nebius_api(prompt)
        return self._parse_json_response(response, [])
    
    async def _generate_full_report(self, executive_summary: str, themes: List[Dict], 
                                  gaps_analysis: Dict, recommendations: List[str], 
                                  summaries: List[Dict], query: str) -> str:
        """Generate the complete report in markdown format"""
        
        # Create structured report
        report_sections = [
            f"# Research Synthesis: {query.title()}",
            f"\n*Analysis of {len(summaries)} research papers*",
            f"\n*Generated on {datetime.now().strftime('%B %d, %Y')}*\n",
            
            "## Executive Summary\n",
            executive_summary,
            
            "\n## Key Themes\n"
        ]
        
        # Add themes
        for i, theme in enumerate(themes, 1):
            report_sections.extend([
                f"\n### {i}. {theme['name']}\n",
                theme['description'],
                f"\n*Contributing papers: {', '.join(theme.get('contributing_papers', []))}*\n"
            ])
        
        # Add gaps and limitations
        report_sections.append("\n## Research Gaps and Limitations\n")
        
        if gaps_analysis.get('gaps'):
            report_sections.append("### Identified Research Gaps\n")
            for gap in gaps_analysis['gaps']:
                priority_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(gap['priority'], "")
                report_sections.extend([
                    f"**{priority_emoji} {gap['description']}**\n",
                    f"*Evidence: {gap['evidence']}*\n"
                ])
        
        if gaps_analysis.get('limitations'):
            report_sections.append("\n### Methodological Limitations\n")
            for limitation in gaps_analysis['limitations']:
                report_sections.extend([
                    f"- **{limitation['description']}**",
                    f"  - Affected papers: {', '.join(limitation['affected_papers'])}",
                    f"  - Impact: {limitation['impact']}\n"
                ])
        
        # Add recommendations
        report_sections.append("\n## Recommendations\n")
        for i, rec in enumerate(recommendations, 1):
            report_sections.append(f"{i}. {rec}\n")
        
        # Add paper summaries section
        report_sections.append("\n## Analyzed Papers\n")
        for i, summary in enumerate(summaries, 1):
            report_sections.extend([
                f"\n### [{i}] {summary['title']}\n",
                f"**Authors:** {', '.join(summary['authors'])}\n",
                f"**Relevance Score:** {summary['relevance_score']:.1f}%\n",
                f"**Summary:** {summary['summary']}\n"
            ])
        
        return '\n'.join(report_sections)
    
    def _format_summaries_for_prompt(self, summaries: List[Dict[str, Any]]) -> str:
        """Format summaries for inclusion in prompts"""
        formatted = []
        for i, summary in enumerate(summaries, 1):
            formatted.append(f"""
Paper {i}: {summary['title']}
Authors: {', '.join(summary['authors'])}
Relevance: {summary['relevance_score']:.1f}%
Summary: {summary['summary']}
Key Findings: {', '.join(summary.get('key_findings', []))}
""")
        return '\n'.join(formatted)
    
    async def _call_nebius_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to Nebius AI Studio"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert research analyst and academic writer. Provide clear, well-structured responses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.4,
            "max_tokens": 2000,
            "top_p": 0.9
        }
        
        async with self.session.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Nebius API error {response.status}: {error_text}")
            
            return await response.json()
    
    def _extract_text_response(self, response: Dict[str, Any]) -> str:
        """Extract text content from API response"""
        try:
            return response['choices'][0]['message']['content'].strip()
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid response format: {e}")
    
    def _parse_json_response(self, response: Dict[str, Any], fallback: Any) -> Any:
        """Parse JSON content from API response"""
        try:
            content = self._extract_text_response(response)
            
            # Clean up response
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            return json.loads(content.strip())
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return fallback
    
    def _create_citations(self, summaries: List[Dict[str, Any]]) -> List[str]:
        """Create IEEE-style citations from paper summaries"""
        citations = []
        for i, summary in enumerate(summaries, 1):
            authors = summary['authors']
            title = summary['title']
            
            # Format authors (first author + et al. if more than 2)
            if len(authors) == 1:
                author_str = authors[0]
            elif len(authors) == 2:
                author_str = f"{authors[0]} and {authors[1]}"
            else:
                author_str = f"{authors[0]} et al."
            
            citation = f"[{i}] {author_str}, \"{title}\""
            
            # Add source and year if available
            if summary.get('source'):
                citation += f", {summary['source']}"
            
            citations.append(citation)
        
        return citations
    
    def _create_fallback_report(self, summaries: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Create fallback report when AI synthesis fails"""
        return {
            'executive_summary': f"Analysis of {len(summaries)} research papers related to {query}. " +
                               "Automated synthesis temporarily unavailable - manual review recommended.",
            'themes': [
                {
                    'name': 'Primary Research Area',
                    'description': f'Research focused on {query} with various methodological approaches.',
                    'contributing_papers': [s['title'] for s in summaries[:3]]
                }
            ],
            'gaps': [
                {
                    'description': 'Synthesis analysis unavailable - manual gap identification needed',
                    'evidence': 'AI processing error',
                    'priority': 'High',
                    'supporting_citations': []
                }
            ],
            'limitations': [],
            'recommendations': [
                'Manual review of papers recommended due to synthesis error',
                'Retry automated analysis with updated system'
            ],
            'citations': self._create_citations(summaries),
            'full_text': f"# Research Analysis: {query}\n\nAutomated synthesis unavailable. Manual review required.",
            'metadata': {
                'query': query,
                'papers_analyzed': len(summaries),
                'generated_at': datetime.now().isoformat(),
                'status': 'fallback'
            }
        }

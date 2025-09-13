import asyncio
import logging
from typing import List, Dict, Any
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class SummaryAgent:
    """AI-powered paper summarization with relevance scoring using Nebius AI Studio"""
    
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
    
    async def summarize_papers(self, papers: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Generate summaries for retrieved papers using Nebius AI"""
        logger.info(f"Summarizing {len(papers)} papers for query: {query}")
        
        # Process papers in batches to avoid rate limits
        batch_size = 3
        summaries = []
        
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            batch_tasks = [self._summarize_single_paper(paper, query) for paper in batch]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Summary generation failed: {result}")
                    continue
                summaries.append(result)
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        return summaries
    
    async def _summarize_single_paper(self, paper: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Generate summary for a single paper"""
        try:
            prompt = self._create_summary_prompt(paper, query)
            
            response = await self._call_nebius_api(prompt)
            summary_data = self._parse_summary_response(response)
            
            return {
                'paper_id': paper['paper_id'],
                'title': paper['title'],
                'authors': paper['authors'],
                'abstract': paper['abstract'],
                'summary': summary_data['summary'],
                'relevance_score': summary_data['relevance_score'],
                'key_findings': summary_data['key_findings'],
                'methodology': summary_data['methodology'],
                'strengths': summary_data['strengths'],
                'weaknesses': summary_data['weaknesses'],
                'doi': paper.get('doi'),
                'url': paper.get('url'),
                'source': paper.get('source')
            }
            
        except Exception as e:
            logger.error(f"Failed to summarize paper {paper['paper_id']}: {e}")
            # Return fallback summary
            return self._create_fallback_summary(paper, query)
    
    def _create_summary_prompt(self, paper: Dict[str, Any], query: str) -> str:
        """Create structured prompt for paper summarization"""
        return f"""
You are an expert academic researcher. Analyze the following research paper and provide a comprehensive summary.

RESEARCH QUERY: {query}

PAPER DETAILS:
Title: {paper['title']}
Authors: {', '.join(paper['authors'])}
Abstract: {paper['abstract']}

Please provide a JSON response with the following structure:
{{
    "summary": "A concise 200-300 word summary focusing on key findings, methodology, and implications",
    "relevance_score": "Score from 0-100 indicating relevance to the query '{query}'",
    "key_findings": ["List of 3-5 key findings or contributions"],
    "methodology": "Brief description of the research methodology used",
    "strengths": ["List of 2-3 paper strengths"],
    "weaknesses": ["List of 2-3 paper limitations or weaknesses"],
    "future_work": ["Suggested areas for future research based on this paper"]
}}

Focus on:
1. How the paper relates to "{query}"
2. Novel contributions and findings
3. Methodological approach and rigor
4. Practical implications and applications
5. Limitations and areas for improvement

Provide only the JSON response, no additional text.
"""
    
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
                    "content": "You are an expert academic researcher and summarization specialist. Always respond with valid JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
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
    
    def _parse_summary_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate Nebius API response"""
        try:
            content = response['choices'][0]['message']['content']
            
            # Clean up response (remove markdown formatting if present)
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            summary_data = json.loads(content)
            
            # Validate required fields
            required_fields = ['summary', 'relevance_score', 'key_findings', 'methodology', 'strengths', 'weaknesses']
            for field in required_fields:
                if field not in summary_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure relevance_score is numeric
            summary_data['relevance_score'] = float(summary_data['relevance_score'])
            
            return summary_data
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse summary response: {e}")
            raise Exception(f"Invalid response format: {e}")
    
    def _create_fallback_summary(self, paper: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Create fallback summary when AI generation fails"""
        # Simple keyword-based relevance scoring
        relevance_score = self._calculate_keyword_relevance(
            paper['title'] + ' ' + paper['abstract'], 
            query
        )
        
        return {
            'paper_id': paper['paper_id'],
            'title': paper['title'],
            'authors': paper['authors'],
            'abstract': paper['abstract'],
            'summary': f"This paper titled '{paper['title']}' presents research relevant to {query}. " +
                      f"The abstract indicates {paper['abstract'][:200]}...",
            'relevance_score': relevance_score,
            'key_findings': ["Automated extraction failed - manual review needed"],
            'methodology': "Not extracted - AI summarization unavailable",
            'strengths': ["Peer-reviewed publication"],
            'weaknesses': ["Summary generation failed"],
            'doi': paper.get('doi'),
            'url': paper.get('url'),
            'source': paper.get('source')
        }
    
    def _calculate_keyword_relevance(self, text: str, query: str) -> float:
        """Calculate relevance score based on keyword matching"""
        text_lower = text.lower()
        query_terms = query.lower().split()
        
        score = 0
        total_terms = len(query_terms)
        
        for term in query_terms:
            if term in text_lower:
                # Count occurrences
                occurrences = text_lower.count(term)
                score += min(occurrences * 10, 30)  # Cap per term
        
        # Normalize to 0-100 scale
        max_possible_score = total_terms * 30
        normalized_score = (score / max_possible_score) * 100 if max_possible_score > 0 else 0
        
        return min(100, normalized_score)

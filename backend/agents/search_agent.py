import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
import json

logger = logging.getLogger(__name__)

class SearchAgent:
    """Advanced search agent with concurrent API queries and error recovery"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.max_retries = 3
        self.timeout = 30
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_papers(self, query: str, max_papers: int = 10) -> List[Dict[str, Any]]:
        """Search for papers across multiple academic APIs concurrently"""
        logger.info(f"Starting concurrent search for: {query}")
        
        # Create search tasks for different APIs
        tasks = [
            self._search_arxiv(query, max_papers // 3),
            self._search_groq(query, max_papers // 3),
            self._search_openalex(query, max_papers // 3),
        ]
        
        # Execute searches concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolidate results and handle errors
        all_papers = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Search API {i} failed: {result}")
                continue
            all_papers.extend(result)
        
        # Deduplicate by DOI/title and sort by relevance
        unique_papers = self._deduplicate_papers(all_papers)
        sorted_papers = sorted(unique_papers, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return sorted_papers[:max_papers]
    
    async def _search_arxiv(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search arXiv API with XML parsing"""
        try:
            url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"arXiv API error: {response.status}")
                    return []
                
                xml_content = await response.text()
                return self._parse_arxiv_xml(xml_content, query)
                
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []
    
    def _parse_arxiv_xml(self, xml_content: str, query: str) -> List[Dict[str, Any]]:
        """Parse arXiv XML response"""
        papers = []
        try:
            root = ET.fromstring(xml_content)
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', namespace):
                title_elem = entry.find('atom:title', namespace)
                summary_elem = entry.find('atom:summary', namespace)
                published_elem = entry.find('atom:published', namespace)
                
                if title_elem is None or summary_elem is None:
                    continue
                
                title = title_elem.text.strip().replace('\n', ' ')
                abstract = summary_elem.text.strip().replace('\n', ' ')
                
                # Extract authors
                authors = []
                for author in entry.findall('atom:author', namespace):
                    name_elem = author.find('atom:name', namespace)
                    if name_elem is not None:
                        authors.append(name_elem.text)
                
                # Extract arXiv ID and create URLs
                arxiv_id = entry.find('atom:id', namespace).text.split('/')[-1]
                
                paper = {
                    'paper_id': f"arxiv_{arxiv_id}",
                    'title': title,
                    'authors': authors,
                    'abstract': abstract,
                    'publication_date': published_elem.text[:10] if published_elem is not None else None,
                    'source': 'arXiv',
                    'url': f"https://arxiv.org/abs/{arxiv_id}",
                    'full_text_url': f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                    'relevance_score': self._calculate_relevance(title + ' ' + abstract, query)
                }
                papers.append(paper)
                
        except ET.ParseError as e:
            logger.error(f"Failed to parse arXiv XML: {e}")
        
        return papers
    
    async def _search_groq(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Groq API using LLM for academic paper discovery"""
        import os
        groq_api_key = os.getenv("GROQ_API_KEY")
        url = "https://api.groq.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json"
        }
        prompt = (
            f"You are an academic research assistant. Given the query: '{query}', "
            "return a list of up to {max_results} recent and relevant academic papers in JSON format: "
            "[{title, authors, abstract, publication_date, doi, url, full_text_url}]. "
            "If you don't know, return an empty list."
        )
        payload = {
            "model": "mixtral-8x7b-32768",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2048,
            "temperature": 0.2
        }
        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Groq API error: {response.status}")
                    return []
                data = await response.json()
                content = data["choices"][0]["message"]["content"]
                # Try to parse JSON from LLM output
                try:
                    papers = json.loads(content)
                except Exception as e:
                    logger.error(f"Groq LLM output parse error: {e}")
                    papers = []
                # Add source and relevance score
                for paper in papers:
                    paper["source"] = "Groq"
                    paper["relevance_score"] = self._calculate_relevance(
                        paper.get("title", "") + " " + paper.get("abstract", ""), query
                    )
                return papers
        except Exception as e:
            logger.error(f"Groq search failed: {e}")
            return []

    async def _search_openalex(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search OpenAlex API"""
        try:
            url = "https://api.openalex.org/works"
            params = {
                'search': query,
                'per-page': max_results,
                'sort': 'relevance_score:desc',
                'filter': 'has_abstract:true'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"OpenAlex API error: {response.status}")
                    return []
                
                data = await response.json()
                return self._parse_openalex_response(data, query)
                
        except Exception as e:
            logger.error(f"OpenAlex search failed: {e}")
            return []
    
    def _parse_openalex_response(self, data: Dict, query: str) -> List[Dict[str, Any]]:
        """Parse OpenAlex API response"""
        papers = []
        
        for work in data.get('results', []):
            if not work.get('title') or not work.get('abstract_inverted_index'):
                continue
            
            # Reconstruct abstract from inverted index
            abstract = self._reconstruct_abstract(work['abstract_inverted_index'])
            
            # Extract authors
            authors = []
            for authorship in work.get('authorships', []):
                author = authorship.get('author', {})
                if author.get('display_name'):
                    authors.append(author['display_name'])
            
            paper = {
                'paper_id': f"openalex_{work['id'].split('/')[-1]}",
                'title': work['title'],
                'authors': authors,
                'abstract': abstract,
                'publication_date': work.get('publication_date', ''),
                'source': 'OpenAlex',
                'url': work.get('doi', ''),
                'full_text_url': work.get('open_access', {}).get('oa_url', ''),
                'relevance_score': self._calculate_relevance(work['title'] + ' ' + abstract, query)
            }
            papers.append(paper)
        
        return papers
    
    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """Reconstruct abstract text from OpenAlex inverted index"""
        if not inverted_index:
            return ""
        
        # Create position-to-word mapping
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        
        # Sort by position and join
        word_positions.sort(key=lambda x: x[0])
        return ' '.join([word for _, word in word_positions])
    
    def _calculate_relevance(self, text: str, query: str) -> float:
        """Calculate relevance score based on keyword matching"""
        text_lower = text.lower()
        query_terms = query.lower().split()
        
        score = 0
        for term in query_terms:
            # Exact match gets higher score
            if term in text_lower:
                score += text_lower.count(term) * 10
            
            # Partial matches
            for word in text_lower.split():
                if term in word or word in term:
                    score += 5
        
        # Normalize by text length
        return min(100, score / len(text_lower) * 1000)
    
    def _deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate papers based on title similarity"""
        unique_papers = []
        seen_titles = set()
        
        for paper in papers:
            title_normalized = paper['title'].lower().strip()
            
            # Check for exact title matches
            if title_normalized in seen_titles:
                continue
            
            # Check for very similar titles (>90% similarity)
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = self._title_similarity(title_normalized, seen_title)
                if similarity > 0.9:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_papers.append(paper)
                seen_titles.add(title_normalized)
        
        return unique_papers
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles using Jaccard similarity"""
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0

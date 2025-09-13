"""
Research Agent - Discovers and retrieves academic papers from multiple sources
"""

import asyncio
import httpx
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from urllib.parse import quote

from ..models.schemas import Paper, Author, PaperSource, ResearchQuery

logger = logging.getLogger(__name__)

class ResearchAgent:
    """Agent responsible for finding and retrieving academic papers"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.sources = {
            PaperSource.ARXIV: self._search_arxiv,
            PaperSource.PUBMED: self._search_pubmed,
            PaperSource.CROSSREF: self._search_crossref,
        }
    
    async def initialize(self):
        """Initialize the research agent"""
        logger.info("Initializing Research Agent...")
        # Test connections to external APIs
        await self._test_connections()
        logger.info("Research Agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.client.aclose()
    
    async def search_papers(self, query: str, max_results: int = 10, sources: Optional[List[PaperSource]] = None) -> List[Paper]:
        """
        Search for papers across multiple academic databases
        
        Args:
            query: Search query string
            max_results: Maximum number of papers to return
            sources: List of sources to search (if None, searches all)
            
        Returns:
            List of Paper objects
        """
        logger.info(f"Searching for papers with query: '{query}' (max_results: {max_results})")
        
        if sources is None:
            sources = list(self.sources.keys())
        
        # Search each source concurrently
        tasks = []
        results_per_source = max(1, max_results // len(sources))
        
        for source in sources:
            if source in self.sources:
                task = self._search_source_safe(source, query, results_per_source)
                tasks.append(task)
        
        # Execute searches concurrently
        source_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate results
        all_papers = []
        for result in source_results:
            if isinstance(result, list):
                all_papers.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Search failed for source: {result}")
        
        # Remove duplicates based on title and DOI
        unique_papers = self._deduplicate_papers(all_papers)
        
        # Sort by relevance (can be enhanced with ML ranking)
        sorted_papers = self._rank_papers(unique_papers, query)
        
        logger.info(f"Found {len(sorted_papers)} unique papers")
        return sorted_papers[:max_results]
    
    async def _search_source_safe(self, source: PaperSource, query: str, max_results: int) -> List[Paper]:
        """Safely search a single source with error handling"""
        try:
            search_func = self.sources[source]
            return await search_func(query, max_results)
        except Exception as e:
            logger.error(f"Error searching {source}: {str(e)}")
            return []
    
    async def _search_arxiv(self, query: str, max_results: int) -> List[Paper]:
        """Search ArXiv for papers"""
        logger.debug(f"Searching ArXiv for: {query}")
        
        # ArXiv API URL
        base_url = "http://export.arxiv.org/api/query"
        encoded_query = quote(query)
        url = f"{base_url}?search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            papers = []
            
            # ArXiv namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                try:
                    # Extract paper information
                    title = entry.find('atom:title', ns).text.strip()
                    summary = entry.find('atom:summary', ns).text.strip()
                    published = entry.find('atom:published', ns).text
                    
                    # Extract authors
                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name = author.find('atom:name', ns).text
                        authors.append(Author(name=name))
                    
                    # Extract links
                    pdf_url = None
                    page_url = None
                    for link in entry.findall('atom:link', ns):
                        if link.get('title') == 'pdf':
                            pdf_url = link.get('href')
                        elif link.get('rel') == 'alternate':
                            page_url = link.get('href')
                    
                    # Extract ArXiv ID
                    arxiv_id = entry.find('atom:id', ns).text.split('/')[-1]
                    
                    paper = Paper(
                        id=f"arxiv:{arxiv_id}",
                        title=title,
                        authors=authors,
                        abstract=summary,
                        url=page_url or f"https://arxiv.org/abs/{arxiv_id}",
                        source=PaperSource.ARXIV,
                        published_date=datetime.fromisoformat(published.replace('Z', '+00:00')),
                        pdf_url=pdf_url,
                    )
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Error parsing ArXiv entry: {e}")
                    continue
            
            logger.debug(f"Found {len(papers)} papers from ArXiv")
            return papers
            
        except Exception as e:
            logger.error(f"ArXiv search failed: {e}")
            return []
    
    async def _search_pubmed(self, query: str, max_results: int) -> List[Paper]:
        """Search PubMed for papers"""
        logger.debug(f"Searching PubMed for: {query}")
        
        # Note: This is a simplified implementation
        # In production, you'd use the official PubMed API with API keys
        try:
            # PubMed eSearch API
            base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json',
                'sort': 'relevance'
            }
            
            response = await self.client.get(base_url, params=params)
            response.raise_for_status()
            search_result = response.json()
            
            if 'esearchresult' not in search_result or 'idlist' not in search_result['esearchresult']:
                return []
            
            pmids = search_result['esearchresult']['idlist']
            if not pmids:
                return []
            
            # Fetch details for found papers
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml',
                'rettype': 'abstract'
            }
            
            fetch_response = await self.client.get(fetch_url, params=fetch_params)
            fetch_response.raise_for_status()
            
            # Parse XML response (simplified)
            papers = []
            # Note: Full PubMed XML parsing would be more complex
            # This is a placeholder that returns basic structure
            for pmid in pmids[:min(len(pmids), 3)]:  # Limit for demo
                paper = Paper(
                    id=f"pubmed:{pmid}",
                    title=f"PubMed Paper {pmid}",  # Would extract from XML
                    authors=[Author(name="Unknown Author")],
                    abstract="Abstract would be parsed from PubMed XML",
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    source=PaperSource.PUBMED,
                    published_date=datetime.now(),
                )
                papers.append(paper)
            
            logger.debug(f"Found {len(papers)} papers from PubMed")
            return papers
            
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []
    
    async def _search_crossref(self, query: str, max_results: int) -> List[Paper]:
        """Search CrossRef for papers"""
        logger.debug(f"Searching CrossRef for: {query}")
        
        try:
            # CrossRef API
            base_url = "https://api.crossref.org/works"
            params = {
                'query': query,
                'rows': max_results,
                'sort': 'relevance',
                'select': 'DOI,title,author,abstract,published,URL'
            }
            
            headers = {
                'User-Agent': 'Agentic-Research-Assistant/1.0 (mailto:research@example.com)'
            }
            
            response = await self.client.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            papers = []
            if 'message' in data and 'items' in data['message']:
                for item in data['message']['items']:
                    try:
                        # Extract title
                        title = item.get('title', ['Unknown Title'])[0]
                        
                        # Extract authors
                        authors = []
                        for author_data in item.get('author', []):
                            name = f"{author_data.get('given', '')} {author_data.get('family', '')}".strip()
                            if name:
                                authors.append(Author(
                                    name=name,
                                    affiliation=author_data.get('affiliation', [{}])[0].get('name')
                                ))
                        
                        # Extract dates
                        published_date = datetime.now()
                        if 'published' in item and 'date-parts' in item['published']:
                            date_parts = item['published']['date-parts'][0]
                            if len(date_parts) >= 3:
                                published_date = datetime(date_parts[0], date_parts[1], date_parts[2])
                            elif len(date_parts) >= 1:
                                published_date = datetime(date_parts[0], 1, 1)
                        
                        paper = Paper(
                            id=f"crossref:{item.get('DOI', 'unknown')}",
                            title=title,
                            authors=authors,
                            abstract=item.get('abstract', 'No abstract available'),
                            doi=item.get('DOI'),
                            url=item.get('URL', f"https://doi.org/{item.get('DOI', '')}"),
                            source=PaperSource.CROSSREF,
                            published_date=published_date,
                        )
                        papers.append(paper)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing CrossRef item: {e}")
                        continue
            
            logger.debug(f"Found {len(papers)} papers from CrossRef")
            return papers
            
        except Exception as e:
            logger.error(f"CrossRef search failed: {e}")
            return []
    
    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers based on title similarity and DOI"""
        seen_dois = set()
        seen_titles = set()
        unique_papers = []
        
        for paper in papers:
            # Check DOI first
            if paper.doi and paper.doi in seen_dois:
                continue
            
            # Check title similarity (simple case-insensitive check)
            title_lower = paper.title.lower().strip()
            if title_lower in seen_titles:
                continue
            
            # Add to unique set
            if paper.doi:
                seen_dois.add(paper.doi)
            seen_titles.add(title_lower)
            unique_papers.append(paper)
        
        return unique_papers
    
    def _rank_papers(self, papers: List[Paper], query: str) -> List[Paper]:
        """Rank papers by relevance to query"""
        # Simple ranking based on query term matches in title and abstract
        query_terms = set(query.lower().split())
        
        def relevance_score(paper: Paper) -> float:
            text = f"{paper.title} {paper.abstract}".lower()
            matches = sum(1 for term in query_terms if term in text)
            return matches / len(query_terms) if query_terms else 0
        
        return sorted(papers, key=relevance_score, reverse=True)
    
    async def _test_connections(self):
        """Test connections to external APIs"""
        test_results = {}
        
        # Test ArXiv
        try:
            response = await self.client.get("http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=1")
            test_results['arxiv'] = response.status_code == 200
        except Exception:
            test_results['arxiv'] = False
        
        # Test CrossRef
        try:
            response = await self.client.get("https://api.crossref.org/works?rows=1")
            test_results['crossref'] = response.status_code == 200
        except Exception:
            test_results['crossref'] = False
        
        logger.info(f"API connection tests: {test_results}")
        return test_results
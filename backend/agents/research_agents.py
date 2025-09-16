"""
Research Agents Module
Adapted from Streamlit code for web integration
Handles paper search, summarization, synthesis, voice generation, and monetization
"""

import os
import requests
import concurrent.futures
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from semanticscholar import SemanticScholar
from openai import OpenAI
import logging
import asyncio
import io

logger = logging.getLogger(__name__)

# Import for voice options
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS not available - voice generation disabled")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available")

# ============== DATA CLASSES ==============
@dataclass
class Paper:
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    url: str = ""
    publication_year: int = None
    source_db: str = ""

@dataclass
class PaperSummary:
    original_paper: Paper
    summary_text: str

@dataclass
class ResearchResult:
    query: str
    papers: List[Paper] = field(default_factory=list)
    summaries: List[PaperSummary] = field(default_factory=list)
    synthesized_report: str = ""
    audio_bytes: Optional[bytes] = None
    nft_status: str = ""
    email_status: str = ""

# ============== AGENT DEFINITIONS ==============
class SearchAndRetrievalAgent:
    def __init__(self):
        self.sch = SemanticScholar()
    
    async def search(self, query: str, max_results: int = 5, min_year: int = None) -> List[Paper]:
        """Search for papers across multiple databases"""
        logger.info(f"Searching for '{query}' with max_results={max_results}, min_year={min_year}")
        papers = []
        
        # Run searches concurrently
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                loop.run_in_executor(executor, self._search_arxiv, query, max_results, min_year),
                loop.run_in_executor(executor, self._search_semantic_scholar, query, max_results, min_year),
                loop.run_in_executor(executor, self._search_openalex, query, max_results, min_year)
            ]
            
            for future in asyncio.as_completed(futures):
                try:
                    result = await future
                    if result:
                        papers.extend(result)
                except Exception as e:
                    logger.error(f"Search failed: {e}")
        
        # Fallback to Google Scholar if not enough results
        if len(papers) < max_results:
            logger.info("Not enough API results, falling back to Google Scholar")
            try:
                google_papers = await loop.run_in_executor(
                    executor, self._scrape_google_scholar, query, max_results, min_year
                )
                if google_papers:
                    papers.extend(google_papers)
            except Exception as e:
                logger.error(f"Google Scholar fallback failed: {e}")
        
        # Remove duplicates and sort by year
        unique_papers = {p.title.lower(): p for p in papers if p.title}.values()
        unique_papers = sorted(unique_papers, key=lambda p: p.publication_year or 0, reverse=True)[:max_results]
        
        logger.info(f"Found {len(unique_papers)} unique papers")
        return list(unique_papers)
    
    def _search_arxiv(self, query: str, max_results: int, min_year: Optional[int]) -> List[Paper]:
        papers = []
        url = f'http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending'
        
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            ns = '{http://www.w3.org/2005/Atom}'
            
            for entry in root.findall(f'{ns}entry'):
                try:
                    year = int(entry.find(f'{ns}published').text.split('-')[0])
                    if min_year and year < min_year:
                        continue
                        
                    papers.append(Paper(
                        title=entry.find(f'{ns}title').text.strip(),
                        authors=[a.find(f'{ns}name').text for a in entry.findall(f'{ns}author')],
                        abstract=entry.find(f'{ns}summary').text.strip(),
                        url=entry.find(f'{ns}id').text,
                        publication_year=year,
                        source_db="arXiv"
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse arXiv entry: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"arXiv search error: {e}")
            
        return papers
    
    def _search_semantic_scholar(self, query: str, max_results: int, min_year: Optional[int]) -> List[Paper]:
        papers = []
        try:
            year_filter = f"{min_year or ''}-" if min_year else None
            results = self.sch.search_paper(query, limit=max_results, year=year_filter)
            
            for item in results:
                try:
                    papers.append(Paper(
                        title=item['title'],
                        authors=[a['name'] for a in item.get('authors', [])],
                        abstract=item.get('abstract', ''),
                        url=item.get('url', ''),
                        publication_year=item.get('year'),
                        source_db="Semantic Scholar"
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse Semantic Scholar result: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")
            
        return papers
    
    def _search_openalex(self, query: str, max_results: int, min_year: Optional[int]) -> List[Paper]:
        papers = []
        url = f"https://api.openalex.org/works?search={query}&per_page={max_results}&sort=publication_date:desc"
        if min_year:
            url += f"&filter=publication_year:>={min_year}"
            
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            for work in data.get('results', []):
                try:
                    # Reconstruct abstract from inverted index
                    abstract = ''
                    if work.get('abstract_inverted_index'):
                        abstract = ' '.join(work['abstract_inverted_index'].keys())
                    
                    papers.append(Paper(
                        title=work.get('title', ''),
                        authors=[a['author']['display_name'] for a in work.get('authorships', [])],
                        abstract=abstract,
                        url=work.get('doi') or work.get('open_access', {}).get('oa_url', ''),
                        publication_year=work.get('publication_year'),
                        source_db="OpenAlex"
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse OpenAlex result: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"OpenAlex search error: {e}")
            
        return papers
    
    def _scrape_google_scholar(self, query: str, max_results: int, min_year: Optional[int]) -> List[Paper]:
        papers = []
        url = f"https://scholar.google.com/scholar?q={query}&hl=en"
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for result in soup.select('.gs_ri')[:max_results]:
                try:
                    title_elem = result.select_one('.gs_rt')
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    
                    gs_a = result.select_one('.gs_a')
                    authors = []
                    year = None
                    
                    if gs_a:
                        gs_a_text = gs_a.text
                        parts = gs_a_text.split(' - ')
                        if parts:
                            authors = parts[0].split(', ')
                        
                        # Extract year
                        year_matches = [int(s) for s in parts if s.strip().isdigit() and len(s.strip()) == 4]
                        if year_matches:
                            year = year_matches[0]
                            if min_year and year < min_year:
                                continue
                    
                    abstract_elem = result.select_one('.gs_rs')
                    abstract = abstract_elem.text.strip() if abstract_elem else ""
                    
                    link_elem = result.select_one('a')
                    link = link_elem.get('href', '') if link_elem else ""
                    
                    papers.append(Paper(
                        title=title,
                        authors=authors,
                        abstract=abstract,
                        url=link,
                        publication_year=year,
                        source_db="Google Scholar"
                    ))
                    
                except Exception as e:
                    logger.warning(f"Failed to parse Google Scholar result: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Google Scholar scraping error: {e}")
            
        return papers

class SummaryAgent:
    def __init__(self, nebius_client: OpenAI):
        self.nebius_client = nebius_client
    
    async def summarize(self, papers: List[Paper]) -> List[PaperSummary]:
        """Summarize a list of papers concurrently"""
        logger.info(f"Summarizing {len(papers)} papers")
        summaries = []
        
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                loop.run_in_executor(executor, self._summarize_paper, paper): paper 
                for paper in papers
            }
            
            for future in asyncio.as_completed(futures):
                try:
                    summary = await future
                    summaries.append(summary)
                except Exception as e:
                    logger.error(f"Could not summarize a paper: {e}")
        
        logger.info(f"Finished summarizing {len(summaries)} papers")
        return summaries
    
    def _summarize_paper(self, paper: Paper) -> PaperSummary:
        """Summarize a single paper using LLM"""
        prompt = f"""Summarize this abstract in 3-4 concise sentences, focusing on key findings, methods, and conclusions. 
        Title: {paper.title} 
        Abstract: {paper.abstract}"""
        
        try:
            resp = self.nebius_client.chat.completions.create(
                model="zai-org/GLM-4.5",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            summary = resp.choices[0].message.content.strip()
            return PaperSummary(paper, summary)
        except Exception as e:
            logger.error(f"Failed to summarize paper '{paper.title}': {e}")
            # Fallback to truncated abstract
            fallback_summary = paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract
            return PaperSummary(paper, fallback_summary)

class SynthesizerAgent:
    def __init__(self, nebius_client: OpenAI):
        self.nebius_client = nebius_client
    
    async def synthesize(self, summaries: List[PaperSummary]) -> str:
        """Synthesize paper summaries into a cohesive report"""
        if not summaries:
            return "No summaries provided."
        
        logger.info(f"Synthesizing report from {len(summaries)} summaries")
        
        summaries_text = "\n\n---\n\n".join([
            f"Title: {s.original_paper.title}\nYear: {s.original_paper.publication_year}\nSummary: {s.summary_text}" 
            for s in summaries
        ])
        
        prompt = f"""Synthesize these research paper summaries into a cohesive report with the following sections: 
        1. Introduction - Brief overview of the research area
        2. Common Themes - What patterns emerge across the papers
        3. Key Findings - Most important discoveries and insights
        4. Conflicting Data/Gaps - Any contradictions or research gaps identified
        5. Conclusion - Overall assessment and future directions
        
        Make the report professional, comprehensive, and well-structured.
        
        Paper Summaries:
        {summaries_text}"""
        
        try:
            resp = self.nebius_client.chat.completions.create(
                model="zai-org/GLM-4.5",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            report = resp.choices[0].message.content.strip()
            logger.info("Report synthesized successfully")
            return report
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            # Fallback to simple concatenation
            fallback_report = "# Research Report\n\n"
            for i, summary in enumerate(summaries, 1):
                fallback_report += f"## Paper {i}: {summary.original_paper.title}\n"
                fallback_report += f"**Year:** {summary.original_paper.publication_year}\n"
                fallback_report += f"**Summary:** {summary.summary_text}\n\n"
            return fallback_report

class VoicePresentationAgent:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key
        self.enabled = False
        self.method = None
        
        # Determine available TTS methods
        if GTTS_AVAILABLE:
            self.method = "gTTS"
            self.enabled = True
        elif PYTTSX3_AVAILABLE:
            self.method = "pyttsx3"
            self.enabled = True
        elif gemini_api_key:
            self.method = "gemini"
            self.enabled = True
    
    def _truncate_text(self, text: str, max_chars: int = 3000) -> str:
        """Truncate text to a reasonable length for TTS"""
        if len(text) <= max_chars:
            return text
        
        # Try to end at a sentence boundary
        truncated = text[:max_chars]
        last_sentence_end = max(
            truncated.rfind('.'),
            truncated.rfind('!'),
            truncated.rfind('?')
        )
        
        if last_sentence_end > max_chars * 0.8:  # If we found a sentence boundary not too far back
            return text[:last_sentence_end+1]
        else:
            return truncated + "..."  # Add ellipsis if we have to cut mid-sentence
    
    async def present(self, report: str) -> Optional[bytes]:
        """Generate audio presentation from text report"""
        logger.info("Generating audio presentation")
        
        if not self.enabled:
            logger.warning("No text-to-speech method available")
            return None
        
        try:
            # Truncate the report to reduce processing time
            truncated_report = self._truncate_text(report)
            
            if len(truncated_report) < len(report):
                logger.info(f"Report truncated for voice generation ({len(truncated_report)} chars instead of {len(report)})")
            
            loop = asyncio.get_event_loop()
            
            # Generate audio based on available method
            if self.method == "gTTS":
                audio_bytes = await loop.run_in_executor(
                    None, self._generate_gtts_audio, truncated_report
                )
                logger.info("Audio ready (using gTTS)")
                return audio_bytes
                
            elif self.method == "pyttsx3":
                audio_bytes = await loop.run_in_executor(
                    None, self._generate_pyttsx3_audio, truncated_report
                )
                logger.info("Audio ready (using pyttsx3)")
                return audio_bytes
                
            elif self.method == "gemini" and self.gemini_api_key:
                # Fallback to gTTS if available
                if GTTS_AVAILABLE:
                    audio_bytes = await loop.run_in_executor(
                        None, self._generate_gtts_audio, truncated_report
                    )
                    logger.info("Audio ready (using gTTS with Gemini key)")
                    return audio_bytes
                else:
                    logger.error("gTTS not available for Gemini fallback")
                    return None
            
        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            return None
    
    def _generate_gtts_audio(self, text: str) -> bytes:
        """Generate audio using gTTS"""
        tts = gTTS(text=text, lang='en', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()
    
    def _generate_pyttsx3_audio(self, text: str) -> bytes:
        """Generate audio using pyttsx3"""
        import tempfile
        engine = pyttsx3.init()
        
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name
        
        engine.save_to_file(text, temp_path)
        engine.runAndWait()
        
        # Read the file as bytes
        with open(temp_path, "rb") as f:
            audio_bytes = f.read()
        
        # Clean up
        os.remove(temp_path)
        return audio_bytes

class MonetizationAgent:
    def __init__(self):
        self.collection_id = os.environ.get('CROSSMINT_COLLECTION_ID', '')
        self.api_key = os.environ.get('CROSSMINT_API_KEY', '')
    
    async def monetize(self, report: str, user_email: str) -> str:
        """Mint Research Report NFT via Crossmint"""
        logger.info(f"Minting Research Report NFT for {user_email}")
        
        # Check if collection ID is set
        if not self.collection_id or not self.api_key:
            return "NFT Minting Failed: Collection ID or API key not set in environment variables."
        
        url = f"https://staging.crossmint.com/api/2022-06-09/collections/{self.collection_id}/nfts"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key
        }
        
        body = {
            "recipient": f"email:{user_email}:polygon",
            "metadata": {
                "name": "Agentic Research Report NFT",
                "description": report[:300] + "..." if len(report) > 300 else report,
                "image": "https://i.imgur.com/v1AmO2I.png"
            }
        }
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.post(url, headers=headers, json=body, timeout=30)
            )
            response.raise_for_status()
            data = response.json()
            nft_id = data.get('id', 'Unknown')
            result = f"NFT minting process started! ID: {nft_id}. Check your email."
            logger.info(f"NFT minted successfully: {nft_id}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"NFT minting failed: {e.response.text if e.response else e}"
            logger.error(error_msg)
            return error_msg

# ============== MAIN RESEARCH ORCHESTRATOR ==============
class ResearchOrchestrator:
    def __init__(self, nebius_api_key: str, gemini_api_key: Optional[str] = None):
        """Initialize all research agents"""
        self.nebius_client = OpenAI(
            api_key=nebius_api_key, 
            base_url="https://api.studio.nebius.com/v1/"
        )
        
        self.search_agent = SearchAndRetrievalAgent()
        self.summary_agent = SummaryAgent(self.nebius_client)
        self.synthesizer_agent = SynthesizerAgent(self.nebius_client)
        self.voice_agent = VoicePresentationAgent(gemini_api_key)
        self.monetization_agent = MonetizationAgent()
    
    async def conduct_research(
        self, 
        query: str, 
        max_results: int = 5, 
        min_year: int = None,
        user_email: Optional[str] = None,
        options: Dict[str, bool] = None
    ) -> ResearchResult:
        """Conduct complete research workflow"""
        
        if options is None:
            options = {
                'use_summary': True,
                'use_synthesis': True,
                'use_voice': False,
                'use_nft': False
            }
        
        result = ResearchResult(query=query)
        
        try:
            # Step 1: Search for papers
            logger.info(f"Step 1: Searching for papers on '{query}'")
            result.papers = await self.search_agent.search(query, max_results, min_year)
            
            if not result.papers:
                logger.warning("No papers found")
                return result
            
            # Step 2: Summarize papers
            if options.get('use_summary', True):
                logger.info("Step 2: Summarizing papers")
                result.summaries = await self.summary_agent.summarize(result.papers)
            else:
                # Create dummy summaries from papers
                result.summaries = [PaperSummary(p, p.abstract) for p in result.papers]
            
            # Step 3: Synthesize report
            if options.get('use_synthesis', True):
                logger.info("Step 3: Synthesizing report")
                result.synthesized_report = await self.synthesizer_agent.synthesize(result.summaries)
            else:
                # Create simple report from summaries
                result.synthesized_report = "\n\n".join([
                    f"**{s.original_paper.title}**\n{s.summary_text}" 
                    for s in result.summaries
                ])
            
            # Step 4: Generate voice presentation
            if options.get('use_voice', False) and self.voice_agent.enabled:
                logger.info("Step 4: Generating voice presentation")
                result.audio_bytes = await self.voice_agent.present(result.synthesized_report)
            
            # Step 5: Mint NFT
            if options.get('use_nft', False) and user_email:
                logger.info("Step 5: Minting NFT")
                result.nft_status = await self.monetization_agent.monetize(
                    result.synthesized_report, user_email
                )
            
            logger.info("Research workflow completed successfully")
            
        except Exception as e:
            logger.error(f"Research workflow failed: {e}")
            raise
        
        return result
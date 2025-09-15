import os
import requests
import concurrent.futures
from dataclasses import dataclass, field
from typing import List, Optional
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from semanticscholar import SemanticScholar
from openai import OpenAI
from elevenlabs.client import ElevenLabs

# Load API keys from environment

# Ensure OpenAI client uses correct env variable
NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY")
os.environ["OPENAI_API_KEY"] = NEBIUS_API_KEY or ""
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
CROSSMINT_API_KEY = os.getenv("CROSSMINT_API_KEY")

nebius_client = OpenAI(api_key=NEBIUS_API_KEY, base_url="https://api.studio.nebius.com/v1/")
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
sch = SemanticScholar()

@dataclass
class Paper:
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    url: str = ""
    publication_year: Optional[int] = None
    source_db: str = ""

@dataclass
class PaperSummary:
    original_paper: Paper
    summary_text: str

class SearchAndRetrievalAgent:
    def search(self, query: str, max_results: int = 5, min_year: int = None) -> List[Paper]:
        papers = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._search_arxiv, query, max_results, min_year),
                executor.submit(self._search_semantic_scholar, query, max_results, min_year),
                executor.submit(self._search_openalex, query, max_results, min_year)
            ]
            for future in concurrent.futures.as_completed(futures):
                papers.extend(future.result() or [])
        if len(papers) < max_results // 2:
            papers.extend(self._scrape_google_scholar(query, max_results - len(papers), min_year))
        unique_papers = {p.title: p for p in papers if p.title}.values()
        unique_papers = sorted(unique_papers, key=lambda p: p.publication_year or 0, reverse=True)[:max_results]
        return list(unique_papers)

    def _search_arxiv(self, query, max_results, min_year):
        papers = []
        start = 0
        while len(papers) < max_results:
            url = f'http://export.arxiv.org/api/query?search_query=all:{query}&start={start}&max_results=10&sortBy=submittedDate&sortOrder=descending'
            try:
                resp = requests.get(url)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)
                ns = '{http://www.w3.org/2005/Atom}'
                for entry in root.findall(f'{ns}entry'):
                    year = int(entry.find(f'{ns}published').text.split('-')[0])
                    if min_year and year < min_year: continue
                    papers.append(Paper(
                        title=entry.find(f'{ns}title').text.strip(),
                        authors=[a.find(f'{ns}name').text for a in entry.findall(f'{ns}author')],
                        abstract=entry.find(f'{ns}summary').text.strip(),
                        url=entry.find(f'{ns}id').text,
                        publication_year=year,
                        source_db="arXiv"
                    ))
                    if len(papers) >= max_results: break
                if len(root.findall(f'{ns}entry')) < 10: break
                start += 10
            except Exception:
                break
        return papers

    def _search_semantic_scholar(self, query, max_results, min_year):
        papers = []
        offset = 0
        while len(papers) < max_results:
            try:
                results = sch.search_paper(query, limit=10, offset=offset, year=f"{min_year or ''}-")
                for item in results:
                    papers.append(Paper(
                        title=item['title'],
                        authors=[a['name'] for a in item['authors']],
                        abstract=item.get('abstract', ''),
                        url=item.get('url', ''),
                        publication_year=item['year'],
                        source_db="Semantic Scholar"
                    ))
                    if len(papers) >= max_results: break
                if len(results) < 10: break
                offset += 10
            except Exception:
                break
        return papers

    def _search_openalex(self, query, max_results, min_year):
        papers = []
        page = 1
        per_page = 10
        while len(papers) < max_results:
            url = f"https://api.openalex.org/works?search={query}&per_page={per_page}&page={page}&sort=publication_date:desc"
            if min_year: url += f"&filter=publication_year:>={min_year}"
            try:
                resp = requests.get(url)
                resp.raise_for_status()
                data = resp.json()
                for work in data.get('results', []):
                    abstract = ' '.join(work.get('abstract_inverted_index', {}).keys()) if work.get('abstract_inverted_index') else ''
                    papers.append(Paper(
                        title=work['title'],
                        authors=[a['author']['display_name'] for a in work['authorships']],
                        abstract=abstract,
                        url=work.get('doi') or work['open_access'].get('oa_url', ''),
                        publication_year=work['publication_year'],
                        source_db="OpenAlex"
                    ))
                    if len(papers) >= max_results: break
                if len(data['results']) < per_page: break
                page += 1
            except Exception:
                break
        return papers

    def _scrape_google_scholar(self, query, max_results, min_year):
        papers = []
        url = f"https://scholar.google.com/scholar?q={query}&hl=en"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(url, headers=headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for result in soup.select('.gs_ri')[:max_results]:
                title = result.select_one('.gs_rt').text
                gs_a = result.select_one('.gs_a').text.split(' - ')
                authors = gs_a[0].split(', ')
                year_str = [int(s) for s in gs_a if s.isdigit() and len(s) == 4]
                year = year_str[0] if year_str else None
                if min_year and year and year < min_year: continue
                abstract = result.select_one('.gs_rs').text
                link = result.select_one('a')['href']
                papers.append(Paper(title=title, authors=authors, abstract=abstract, url=link, publication_year=year, source_db="Google Scholar"))
        except Exception:
            pass
        return papers

class SummaryAgent:
    def summarize(self, papers: List[Paper]) -> List[PaperSummary]:
        summaries = []
        for paper in papers:
            prompt = f"""
            Summarize this abstract (3-4 sentences): Key findings, methods, conclusions.
            Title: {paper.title}
            Abstract: {paper.abstract}
            """
            try:
                resp = nebius_client.chat.completions.create(
                    model="meta-llama/Meta-Llama-3.1-70B-Instruct",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200
                )
                summary = resp.choices[0].message.content.strip()
                summaries.append(PaperSummary(paper, summary))
            except Exception:
                summaries.append(PaperSummary(paper, "Summary failed."))
        return summaries

class SynthesizerAgent:
    def synthesize(self, summaries: List[PaperSummary]) -> str:
        if not summaries: return "No summaries."
        summaries_text = "\n\n---\n\n".join([f"Title: {s.original_paper.title}\nSummary: {s.summary_text}" for s in summaries])
        prompt = f"""
        Synthesize into report:
        1. Introduction
        2. Common Themes
        3. Conflicting Data/Gaps
        4. Conclusion
        Summaries: {summaries_text}
        """
        try:
            resp = nebius_client.chat.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            report = resp.choices[0].message.content.strip()
            return report
        except Exception:
            return "Failed."

class VoicePresentationAgent:
    def present(self, report: str) -> bytes:
        try:
            audio = eleven_client.text_to_speech.convert(
                text=report,
                voice_id="EXAVITQu4vr4xnSDxMaL",  # Rachel
                model="eleven_multilingual_v2"
            )
            audio_bytes = b''.join(audio)
            return audio_bytes
        except Exception:
            return b''

class MonetizationAgent:
    def monetize(self, report: str, user_email: str) -> str:
        if not user_email:
            return "No email provided for NFT recipient."
        url = "https://staging.crossmint.com/api/2022-06-09/collections/default-polygon/nfts"
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": CROSSMINT_API_KEY
        }
        body = {
            "recipient": f"email:{user_email}:polygon",
            "metadata": {
                "name": "Research Report NFT",
                "description": report[:200] + "...",
                "image": "https://via.placeholder.com/150"
            },
            "sendNotification": True,
            "locale": "en-US",
            "reuploadLinkedFiles": True,
            "compressed": True
        }
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            nft_id = data.get('id', 'Unknown')
            status = data.get('onChain', {}).get('status', 'pending')
            return f"NFT minted successfully: {nft_id} (check your email)"
        except requests.exceptions.RequestException as e:
            return "NFT mint failed."
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Lazy imports for optional integrations
try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None

try:
    import faiss
    import numpy as np
except Exception:  # pragma: no cover
    faiss = None
    np = None

# Optional Gemini/LLM integration via langchain_google_genai
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    has_gemini = True
except Exception:  # pragma: no cover
    ChatGoogleGenerativeAI = None
    has_gemini = False


class PDFAnalysisAgent:
    """
    Lightweight PDF analysis agent replacing the Gradio app functionality.

    Responsibilities:
    - Extract text from PDFs (per-page + sentence-level)
    - Build a FAISS index using SentenceTransformer embeddings
    - Provide a query method that retrieves relevant passages and (optionally)
      calls Gemini (if available) to produce a short answer.

    The implementation is defensive: if optional deps are missing it still
    provides retrieval context instead of failing loudly.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key
        self.embedding_model = None
        self.faiss_index = None
        self.sentence_metadata: List[Dict[str, Any]] = []

    async def initialize_embeddings(self):
        """Load SentenceTransformer model if available and not yet loaded."""
        if self.embedding_model is not None:
            return
        if SentenceTransformer is None:
            raise RuntimeError("SentenceTransformer is not installed in the environment")
        # Load synchronously (fast) but expose as async for caller convenience
        try:
            logger.info("Loading embedding model 'all-MiniLM-L6-v2'")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded")
        except Exception as e:
            logger.exception("Failed to initialize embedding model")
            raise

    async def analyze_pdf(self, pdf_path: str, query: Optional[str] = None) -> Dict[str, Any]:
        """High-level pipeline used by upload handler.

        Steps:
        1. Extract text -> sentence list
        2. Build FAISS index (in-memory)
        3. If query provided, run retrieval and optionally call Gemini
        """
        if fitz is None:
            raise RuntimeError("PyMuPDF (fitz) is not installed in the environment")

        logger.info(f"Starting analysis for: {pdf_path}")

        extraction = await asyncio.get_event_loop().run_in_executor(None, self._extract_pdf_content_sync, pdf_path)

        # Build embeddings / FAISS index
        if np is None or faiss is None:
            logger.warning("faiss or numpy not available - skipping index build")
            rag_info = {'index_built': False}
        else:
            await self.initialize_embeddings()
            rag_info = await asyncio.get_event_loop().run_in_executor(None, self._build_rag_index_sync, extraction['sentences'])

        answer = None
        if query:
            try:
                answer = await self.ask_question(query)
            except Exception as e:
                logger.exception(f"Failed to answer query: {e}")
                answer = None

        result = {
            'pdf_metadata': {
                'file_path': pdf_path,
                'total_pages': extraction.get('total_pages', 0),
                'total_sentences': len(extraction.get('sentences', [])),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'extraction': extraction,
            'rag_index_info': rag_info,
            'answer': answer
        }

        return result

    def _extract_pdf_content_sync(self, pdf_path: str) -> Dict[str, Any]:
        """Synchronous PDF extraction using PyMuPDF. Returns a dict with sentences.

        Each sentence is a dict: {id, text, page}
        """
        if fitz is None:
            raise RuntimeError("PyMuPDF (fitz) not available")

        doc = fitz.open(pdf_path)
        sentences: List[Dict[str, Any]] = []
        pages: List[Dict[str, Any]] = []

        try:
            for pnum in range(len(doc)):
                page = doc[pnum]
                text = page.get_text("text") or ""
                # split into simple sentences
                parts = [s.strip() for s in _split_sentences(text) if s.strip()]
                page_sentences: List[Dict[str, Any]] = []
                for s in parts:
                    sid = len(sentences)
                    item = {'id': sid, 'text': s, 'page': pnum + 1}
                    sentences.append(item)
                    page_sentences.append(item)

                pages.append({'page_num': pnum + 1, 'sentences': page_sentences, 'text': text})

            return {'total_pages': len(pages), 'sentences': sentences, 'pages_data': pages}
        finally:
            try:
                doc.close()
            except Exception:
                pass

    def _build_rag_index_sync(self, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronous FAISS build using SentenceTransformer and faiss."""
        texts = [s['text'] for s in sentences]
        if not texts:
            return {'index_built': False, 'size': 0}

        if self.embedding_model is None:
            raise RuntimeError('Embedding model not initialized')

        emb = self.embedding_model.encode(texts, show_progress_bar=False)
        arr = np.asarray(emb, dtype='float32')
        faiss.normalize_L2(arr)
        dim = arr.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(arr)

        # store
        self.faiss_index = index
        self.sentence_metadata = sentences

        return {'index_built': True, 'size': len(sentences), 'dimension': dim}

    async def query_rag_index(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Return top-k similar sentences for the query."""
        if self.faiss_index is None or self.embedding_model is None:
            raise RuntimeError('RAG index not initialized')

        q_emb = self.embedding_model.encode([query])
        q = np.asarray(q_emb, dtype='float32')
        faiss.normalize_L2(q)
        scores, idxs = self.faiss_index.search(q, top_k)

        results: List[Dict[str, Any]] = []
        for score, idx in zip(scores[0], idxs[0]):
            if idx < len(self.sentence_metadata):
                item = dict(self.sentence_metadata[idx])
                item['score'] = float(score)
                results.append(item)
        return results

    async def ask_question(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve context and optionally use Gemini to form an answer.

        Returns a dict with: {answer, context, sources}
        """
        # If index not built, return message
        if self.faiss_index is None:
            return {'answer': None, 'context': '', 'sources': []}

        hits = await self.query_rag_index(query, top_k=top_k)
        context = "\n\n".join([h['text'] for h in hits])
        sources = [{'id': h['id'], 'page': h['page'], 'score': h.get('score', 0.0)} for h in hits]

        # Only attempt Gemini / Google LLM if an explicit GOOGLE_API_KEY env var is present.
        # This avoids accidental calls with invalid keys during startup.
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if has_gemini and ChatGoogleGenerativeAI is not None and google_api_key:
            try:
                logger.info("Invoking Gemini LLM for answer synthesis")
                llm = ChatGoogleGenerativeAI(model='gemini-1.5-flash', temperature=0, max_output_tokens=512, google_api_key=google_api_key)
                prompt = f"""
You are a helpful assistant. Answer the question based only on the context below.

Context:
{context}

Question:
{query}

If the answer is not in the context, say "I don't know".
"""
                response = llm.invoke(prompt)
                # Many wrappers return `.content` or similar; try to be defensive
                answer_text = getattr(response, 'content', None) or getattr(response, 'text', None) or str(response)
            except Exception as e:  # pragma: no cover
                logger.exception("Gemini call failed")
                answer_text = None
        else:
            # Fallback: return the retrieved context as the "answer" so frontend can display
            answer_text = context

        return {'answer': answer_text, 'context': context, 'sources': sources}

    # Utilities used by upload handler
    def get_sentence_by_id(self, sentence_id: int) -> Optional[Dict[str, Any]]:
        if 0 <= sentence_id < len(self.sentence_metadata):
            return self.sentence_metadata[sentence_id]
        return None

    def search_sentences(self, term: str) -> List[Dict[str, Any]]:
        q = term.lower()
        return [s for s in self.sentence_metadata if q in s['text'].lower()]


# small helper
def _split_sentences(text: str) -> List[str]:
    # basic splitter, can be improved/replaced
    import re

    parts = re.split(r'(?<=[.!?])\s+', text)
    return parts

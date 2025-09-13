import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import fitz  # PyMuPDF
import re
import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

class PDFAnalysisAgent:
    """
    Advanced PDF analysis agent with citation mapping and RAG pipeline
    Handles deep PDF parsing, citation extraction, and literature review generation
    """
    
    def __init__(self, nebius_api_key: str):
        self.nebius_api_key = nebius_api_key
        self.embedding_model = None
        self.faiss_index = None
        self.sentence_metadata = []
        self.citation_patterns = [
            r'\[(\d+)\]',  # [1], [2], etc.
            r'$$(\d+)$$',  # (1), (2), etc.
            r'(\d+)\.',    # 1., 2., etc. at start of line
        ]
        
    async def initialize_embeddings(self):
        """Initialize sentence transformer model for embeddings"""
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise
    
    async def analyze_pdf(self, pdf_path: str, query: str) -> Dict[str, Any]:
        """
        Complete PDF analysis pipeline:
        1. Extract text with bounding boxes
        2. Parse citations and references
        3. Build RAG index
        4. Generate literature review
        5. Identify gaps and limitations
        """
        logger.info(f"Starting PDF analysis for: {pdf_path}")
        
        try:
            # Step 1: Extract text and structure
            extraction_result = await self._extract_pdf_content(pdf_path)
            
            # Step 2: Parse citations and build reference map
            citation_map = await self._parse_citations_and_references(extraction_result)
            
            # Step 3: Build RAG pipeline
            rag_index = await self._build_rag_index(extraction_result['sentences'])
            
            # Step 4: Generate literature review
            literature_review = await self._generate_literature_review(
                extraction_result, citation_map, query
            )
            
            # Step 5: Identify gaps and limitations
            gaps_analysis = await self._analyze_gaps_and_limitations(
                extraction_result, citation_map, query
            )
            
            return {
                'pdf_metadata': {
                    'file_path': pdf_path,
                    'total_pages': extraction_result['total_pages'],
                    'total_sentences': len(extraction_result['sentences']),
                    'total_citations': len(citation_map['citations']),
                    'analysis_timestamp': datetime.now().isoformat()
                },
                'extraction': extraction_result,
                'citations': citation_map,
                'literature_review': literature_review,
                'gaps_analysis': gaps_analysis,
                'rag_index_info': {
                    'total_embeddings': len(self.sentence_metadata),
                    'embedding_dimension': 384  # all-MiniLM-L6-v2 dimension
                }
            }
            
        except Exception as e:
            logger.error(f"PDF analysis failed: {e}")
            raise
    
    async def _extract_pdf_content(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text with normalized bounding boxes and sentence segmentation"""
        try:
            doc = fitz.open(pdf_path)
            sentences = []
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_dict = page.get_text("dict")
                page_width = page.rect.width
                page_height = page.rect.height
                
                page_sentences = []
                
                # Extract text blocks and process sentences
                for block in page_dict["blocks"]:
                    if "lines" in block:
                        for line in block["lines"]:
                            line_text = ""
                            line_bbox = None
                            
                            for span in line["spans"]:
                                line_text += span["text"]
                                if line_bbox is None:
                                    line_bbox = span["bbox"]
                                else:
                                    # Expand bounding box
                                    line_bbox = [
                                        min(line_bbox[0], span["bbox"][0]),
                                        min(line_bbox[1], span["bbox"][1]),
                                        max(line_bbox[2], span["bbox"][2]),
                                        max(line_bbox[3], span["bbox"][3])
                                    ]
                            
                            # Split into sentences
                            if line_text.strip():
                                line_sentences = self._split_into_sentences(line_text)
                                
                                for i, sentence in enumerate(line_sentences):
                                    if len(sentence.strip()) > 10:  # Filter very short sentences
                                        # Normalize bounding box to percentages
                                        normalized_bbox = {
                                            'left': line_bbox[0] / page_width,
                                            'top': line_bbox[1] / page_height,
                                            'width': (line_bbox[2] - line_bbox[0]) / page_width,
                                            'height': (line_bbox[3] - line_bbox[1]) / page_height
                                        }
                                        
                                        sentence_data = {
                                            'id': len(sentences),
                                            'text': sentence.strip(),
                                            'page': page_num + 1,
                                            'bbox': normalized_bbox,
                                            'absolute_bbox': line_bbox,
                                            'sentence_index_in_line': i
                                        }
                                        
                                        sentences.append(sentence_data)
                                        page_sentences.append(sentence_data)
                
                pages_data.append({
                    'page_number': page_num + 1,
                    'sentences': page_sentences,
                    'dimensions': {'width': page_width, 'height': page_height}
                })
            
            doc.close()
            
            return {
                'sentences': sentences,
                'pages': pages_data,
                'total_pages': len(doc)
            }
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex patterns"""
        # Simple sentence splitting - can be enhanced with NLTK or spaCy
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)
        
        # Clean and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 5:
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    async def _parse_citations_and_references(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse in-text citations and build reference mapping"""
        citations = {}
        references = {}
        citances = []  # Sentences that contain citations
        
        # Find reference section
        reference_section = self._find_reference_section(extraction_result['sentences'])
        
        if reference_section:
            references = self._parse_reference_section(reference_section)
        
        # Find in-text citations
        for sentence in extraction_result['sentences']:
            sentence_citations = self._extract_citations_from_sentence(sentence['text'])
            
            if sentence_citations:
                citances.append({
                    'sentence_id': sentence['id'],
                    'sentence_text': sentence['text'],
                    'page': sentence['page'],
                    'citations': sentence_citations,
                    'bbox': sentence['bbox']
                })
                
                for citation in sentence_citations:
                    if citation not in citations:
                        citations[citation] = []
                    citations[citation].append(sentence['id'])
        
        return {
            'citations': citations,
            'references': references,
            'citances': citances,
            'reference_section': reference_section
        }
    
    def _find_reference_section(self, sentences: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Find and extract the references section"""
        reference_keywords = ['references', 'bibliography', 'works cited', 'literature cited']
        
        reference_start = None
        for i, sentence in enumerate(sentences):
            text_lower = sentence['text'].lower().strip()
            
            # Look for reference section headers
            if any(keyword in text_lower for keyword in reference_keywords):
                if len(text_lower) < 50:  # Likely a section header
                    reference_start = i + 1
                    break
        
        if reference_start:
            # Extract references until end of document or next major section
            reference_sentences = []
            for i in range(reference_start, len(sentences)):
                sentence = sentences[i]
                text = sentence['text'].strip()
                
                # Stop at next major section (simple heuristic)
                if (len(text) < 50 and 
                    any(word in text.lower() for word in ['appendix', 'acknowledgment', 'conclusion'])):
                    break
                
                reference_sentences.append(sentence)
            
            return reference_sentences
        
        return None
    
    def _parse_reference_section(self, reference_sentences: List[Dict[str, Any]]) -> Dict[str, str]:
        """Parse reference section into citation ID -> bibliography entry mapping"""
        references = {}
        current_ref_id = None
        current_ref_text = ""
        
        for sentence in reference_sentences:
            text = sentence['text'].strip()
            
            # Look for reference number at start of line
            ref_match = re.match(r'^\[?(\d+)\]?\s*(.+)', text)
            if ref_match:
                # Save previous reference
                if current_ref_id and current_ref_text:
                    references[current_ref_id] = current_ref_text.strip()
                
                # Start new reference
                current_ref_id = ref_match.group(1)
                current_ref_text = ref_match.group(2)
            else:
                # Continue current reference
                if current_ref_id:
                    current_ref_text += " " + text
        
        # Save last reference
        if current_ref_id and current_ref_text:
            references[current_ref_id] = current_ref_text.strip()
        
        return references
    
    def _extract_citations_from_sentence(self, text: str) -> List[str]:
        """Extract citation numbers from sentence text"""
        citations = []
        
        for pattern in self.citation_patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        return list(set(citations))  # Remove duplicates
    
    async def _build_rag_index(self, sentences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build FAISS index for RAG pipeline"""
        if not self.embedding_model:
            await self.initialize_embeddings()
        
        # Extract sentence texts
        sentence_texts = [s['text'] for s in sentences]
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(sentence_texts)} sentences")
        embeddings = self.embedding_model.encode(sentence_texts, show_progress_bar=True)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.faiss_index.add(embeddings.astype('float32'))
        
        # Store metadata
        self.sentence_metadata = sentences
        
        logger.info(f"FAISS index built with {len(sentences)} sentences")
        
        return {
            'index_size': len(sentences),
            'embedding_dimension': dimension,
            'index_type': 'FAISS_IndexFlatIP'
        }
    
    async def query_rag_index(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Query RAG index for relevant sentences"""
        if not self.faiss_index or not self.embedding_model:
            raise ValueError("RAG index not initialized")
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search index
        scores, indices = self.faiss_index.search(query_embedding.astype('float32'), top_k)
        
        # Return results with metadata
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.sentence_metadata):
                result = self.sentence_metadata[idx].copy()
                result['similarity_score'] = float(score)
                result['rank'] = i + 1
                results.append(result)
        
        return results
    
    async def _generate_literature_review(self, extraction_result: Dict[str, Any], 
                                        citation_map: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Generate literature review using RAG pipeline"""
        try:
            # Query RAG index for relevant content
            relevant_sentences = await self.query_rag_index(query, top_k=10)
            
            # Build context from relevant sentences and citations
            context_parts = []
            for sentence in relevant_sentences:
                context_parts.append(f"[Sentence {sentence['id']}, Page {sentence['page']}]: {sentence['text']}")
            
            context = "\n".join(context_parts)
            
            # Generate literature review using LLM
            review_prompt = f"""
Based on the following content from a research paper, generate a comprehensive literature review focused on "{query}".

RELEVANT CONTENT:
{context}

AVAILABLE CITATIONS:
{json.dumps(citation_map['references'], indent=2)}

Generate a literature review that:
1. Synthesizes the key findings related to "{query}"
2. Identifies the main themes and approaches
3. Uses proper in-text citations [n] where appropriate
4. Highlights connections between different parts of the paper
5. Maintains academic writing style

Return a JSON response with:
{{
    "literature_review": "The comprehensive literature review text with citations",
    "key_themes": ["List of 3-5 main themes identified"],
    "cited_references": ["List of citation numbers used in the review"],
    "synthesis_quality": "Assessment of how well the paper synthesizes existing literature"
}}
"""
            
            # Call LLM API (placeholder - would use actual Nebius API)
            review_response = await self._call_llm_for_review(review_prompt)
            
            return {
                'literature_review': review_response.get('literature_review', ''),
                'key_themes': review_response.get('key_themes', []),
                'cited_references': review_response.get('cited_references', []),
                'synthesis_quality': review_response.get('synthesis_quality', ''),
                'relevant_sentences': relevant_sentences,
                'context_used': context
            }
            
        except Exception as e:
            logger.error(f"Literature review generation failed: {e}")
            return self._create_fallback_literature_review(extraction_result, query)
    
    async def _analyze_gaps_and_limitations(self, extraction_result: Dict[str, Any], 
                                          citation_map: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Analyze research gaps and limitations with evidence linking"""
        try:
            # Find sentences discussing limitations, gaps, or future work
            limitation_keywords = [
                'limitation', 'limited', 'gap', 'future work', 'future research',
                'not addressed', 'beyond scope', 'insufficient', 'lack of',
                'further investigation', 'remains unclear', 'needs more'
            ]
            
            limitation_sentences = []
            for sentence in extraction_result['sentences']:
                text_lower = sentence['text'].lower()
                if any(keyword in text_lower for keyword in limitation_keywords):
                    limitation_sentences.append(sentence)
            
            # Analyze citances for gap identification
            gap_evidence = []
            for citance in citation_map['citances']:
                # Look for patterns indicating gaps
                text_lower = citance['sentence_text'].lower()
                if any(word in text_lower for word in ['however', 'but', 'although', 'despite']):
                    gap_evidence.append({
                        'sentence_id': citance['sentence_id'],
                        'text': citance['sentence_text'],
                        'page': citance['page'],
                        'citations': citance['citations'],
                        'gap_type': 'methodological' if 'method' in text_lower else 'conceptual'
                    })
            
            # Generate structured gaps analysis
            gaps_prompt = f"""
Analyze the following sentences from a research paper to identify research gaps and limitations related to "{query}".

LIMITATION SENTENCES:
{json.dumps([s['text'] for s in limitation_sentences], indent=2)}

GAP EVIDENCE:
{json.dumps([g['text'] for g in gap_evidence], indent=2)}

Identify specific research gaps with:
1. Clear description of the gap
2. Evidence from the text (cite sentence IDs)
3. Priority level (High/Medium/Low)
4. Type of gap (methodological, conceptual, empirical, etc.)

Return JSON:
{{
    "gaps": [
        {{
            "description": "Clear gap description",
            "evidence_sentence_ids": [list of sentence IDs],
            "evidence_text": "Specific text supporting this gap",
            "priority": "High|Medium|Low",
            "gap_type": "methodological|conceptual|empirical|theoretical",
            "page_references": [list of page numbers]
        }}
    ],
    "overall_assessment": "Summary of the paper's coverage and main gaps"
}}
"""
            
            gaps_response = await self._call_llm_for_gaps(gaps_prompt)
            
            return {
                'gaps': gaps_response.get('gaps', []),
                'overall_assessment': gaps_response.get('overall_assessment', ''),
                'limitation_sentences': limitation_sentences,
                'gap_evidence': gap_evidence,
                'analysis_metadata': {
                    'limitation_sentences_found': len(limitation_sentences),
                    'gap_evidence_found': len(gap_evidence),
                    'total_sentences_analyzed': len(extraction_result['sentences'])
                }
            }
            
        except Exception as e:
            logger.error(f"Gaps analysis failed: {e}")
            return self._create_fallback_gaps_analysis()
    
    async def _call_llm_for_review(self, prompt: str) -> Dict[str, Any]:
        """Call LLM API for literature review generation (placeholder)"""
        # Placeholder for actual Nebius API call
        await asyncio.sleep(1)  # Simulate API call
        
        return {
            'literature_review': f"This paper provides a comprehensive analysis of quantum computing ethics, building on foundational work in the field [1][2]. The authors synthesize multiple perspectives on privacy concerns, algorithmic fairness, and governance challenges. The literature review demonstrates strong engagement with existing scholarship while identifying key areas for future development.",
            'key_themes': [
                'Privacy and Security Implications',
                'Algorithmic Fairness and Bias',
                'Governance and Regulation',
                'Societal Impact Assessment'
            ],
            'cited_references': ['1', '2', '3'],
            'synthesis_quality': 'High - demonstrates comprehensive understanding of existing literature'
        }
    
    async def _call_llm_for_gaps(self, prompt: str) -> Dict[str, Any]:
        """Call LLM API for gaps analysis (placeholder)"""
        # Placeholder for actual Nebius API call
        await asyncio.sleep(1)  # Simulate API call
        
        return {
            'gaps': [
                {
                    'description': 'Limited empirical validation of proposed ethical frameworks',
                    'evidence_sentence_ids': [45, 67],
                    'evidence_text': 'The authors acknowledge that their framework requires empirical testing in real-world quantum computing environments.',
                    'priority': 'High',
                    'gap_type': 'empirical',
                    'page_references': [7, 9]
                },
                {
                    'description': 'Insufficient consideration of international regulatory differences',
                    'evidence_sentence_ids': [23],
                    'evidence_text': 'The paper focuses primarily on US regulatory context without adequate consideration of international variations.',
                    'priority': 'Medium',
                    'gap_type': 'conceptual',
                    'page_references': [4]
                }
            ],
            'overall_assessment': 'The paper provides a solid theoretical foundation but would benefit from empirical validation and broader international perspective.'
        }
    
    def _create_fallback_literature_review(self, extraction_result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Create fallback literature review when LLM generation fails"""
        return {
            'literature_review': f"Literature review generation failed. Manual analysis of {len(extraction_result['sentences'])} sentences required for comprehensive review of {query}.",
            'key_themes': ['Manual analysis required'],
            'cited_references': [],
            'synthesis_quality': 'Analysis unavailable - system error',
            'relevant_sentences': [],
            'context_used': ''
        }
    
    def _create_fallback_gaps_analysis(self) -> Dict[str, Any]:
        """Create fallback gaps analysis when LLM generation fails"""
        return {
            'gaps': [
                {
                    'description': 'Gaps analysis unavailable due to system error',
                    'evidence_sentence_ids': [],
                    'evidence_text': 'Manual review required',
                    'priority': 'High',
                    'gap_type': 'system',
                    'page_references': []
                }
            ],
            'overall_assessment': 'Manual gaps analysis required due to system limitations',
            'limitation_sentences': [],
            'gap_evidence': [],
            'analysis_metadata': {
                'limitation_sentences_found': 0,
                'gap_evidence_found': 0,
                'total_sentences_analyzed': 0
            }
        }
    
    def get_sentence_by_id(self, sentence_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve sentence by ID for citation linking"""
        if 0 <= sentence_id < len(self.sentence_metadata):
            return self.sentence_metadata[sentence_id]
        return None
    
    def get_sentences_by_page(self, page_number: int) -> List[Dict[str, Any]]:
        """Get all sentences from a specific page"""
        return [s for s in self.sentence_metadata if s['page'] == page_number]
    
    def search_sentences(self, search_term: str) -> List[Dict[str, Any]]:
        """Search sentences by text content"""
        results = []
        search_lower = search_term.lower()
        
        for sentence in self.sentence_metadata:
            if search_lower in sentence['text'].lower():
                results.append(sentence)
        
        return results

import asyncio
import logging
from typing import Dict, Any, Optional
import aiofiles
import os
import uuid
from datetime import datetime
from .pdf_analysis_agent import PDFAnalysisAgent
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PDFUploadHandler:
    """
    Handles PDF file uploads and coordinates with PDF analysis agent
    Manages file storage, validation, and analysis workflow
    """
    
    def __init__(self, upload_dir: str = "uploads", nebius_api_key: str = None):
        self.upload_dir = upload_dir
        self.nebius_api_key = nebius_api_key
        self.pdf_analyzer = PDFAnalysisAgent(nebius_api_key) if nebius_api_key else None
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {'.pdf'}
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
    
    async def handle_pdf_upload(self, file_content: bytes, filename: str, 
                               query: str, user_id: str = None) -> Dict[str, Any]:
        """
        Complete PDF upload and analysis workflow
        """
        try:
            # Validate file
            validation_result = await self._validate_pdf_file(file_content, filename)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'error_type': 'validation'
                }
            
            # Save file
            file_path = await self._save_uploaded_file(file_content, filename, user_id)
            
            # Initialize PDF analyzer if not already done
            if not self.pdf_analyzer:
                self.pdf_analyzer = PDFAnalysisAgent(self.nebius_api_key)
            
            await self.pdf_analyzer.initialize_embeddings()
            
            # Analyze PDF
            analysis_result = await self.pdf_analyzer.analyze_pdf(file_path, query)
            
            # Add upload metadata
            analysis_result['upload_metadata'] = {
                'original_filename': filename,
                'file_path': file_path,
                'file_size': len(file_content),
                'upload_timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'query': query
            }
            
            return {
                'success': True,
                'analysis_result': analysis_result,
                'file_info': {
                    'filename': filename,
                    'file_path': file_path,
                    'file_size': len(file_content)
                }
            }
            
        except Exception as e:
            logger.error(f"PDF upload and analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'processing'
            }
    
    async def _validate_pdf_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded PDF file"""
        try:
            # Check file extension
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in self.allowed_extensions:
                return {
                    'valid': False,
                    'error': f'Invalid file type. Only PDF files are allowed. Got: {file_ext}'
                }
            
            # Check file size
            if len(file_content) > self.max_file_size:
                return {
                    'valid': False,
                    'error': f'File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB'
                }
            
            # Check if file is empty
            if len(file_content) == 0:
                return {
                    'valid': False,
                    'error': 'File is empty'
                }
            
            # Basic PDF header validation
            if not file_content.startswith(b'%PDF-'):
                return {
                    'valid': False,
                    'error': 'Invalid PDF file format'
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'File validation error: {str(e)}'
            }
    
    async def _save_uploaded_file(self, file_content: bytes, filename: str, 
                                 user_id: str = None) -> str:
        """Save uploaded file to disk with unique filename"""
        try:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = self._sanitize_filename(filename)
            
            unique_filename = f"{timestamp}_{file_id}_{safe_filename}"
            file_path = os.path.join(self.upload_dir, unique_filename)
            
            # Save file asynchronously
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            logger.info(f"PDF file saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file: {e}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove or replace unsafe characters
        import re
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Limit length
        if len(safe_filename) > 100:
            name, ext = os.path.splitext(safe_filename)
            safe_filename = name[:95] + ext
        
        return safe_filename
    
    async def get_pdf_highlights(self, file_path: str, sentence_ids: List[int]) -> Dict[str, Any]:
        """Get highlighting information for specific sentences in PDF"""
        try:
            if not self.pdf_analyzer:
                raise ValueError("PDF analyzer not initialized")
            
            highlights = []
            for sentence_id in sentence_ids:
                sentence = self.pdf_analyzer.get_sentence_by_id(sentence_id)
                if sentence:
                    highlights.append({
                        'sentence_id': sentence_id,
                        'page': sentence['page'],
                        'bbox': sentence['bbox'],
                        'text': sentence['text']
                    })
            
            return {
                'success': True,
                'highlights': highlights,
                'file_path': file_path
            }
            
        except Exception as e:
            logger.error(f"Failed to get PDF highlights: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def search_pdf_content(self, file_path: str, query: str, top_k: int = 10) -> Dict[str, Any]:
        """Search PDF content using RAG pipeline"""
        try:
            if not self.pdf_analyzer:
                raise ValueError("PDF analyzer not initialized")
            
            results = await self.pdf_analyzer.query_rag_index(query, top_k)
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'total_results': len(results)
            }
            
        except Exception as e:
            logger.error(f"PDF content search failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cleanup_uploaded_file(self, file_path: str) -> bool:
        """Clean up uploaded file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {e}")
            return False
    
    def get_upload_stats(self) -> Dict[str, Any]:
        """Get statistics about uploaded files"""
        try:
            files = os.listdir(self.upload_dir)
            pdf_files = [f for f in files if f.endswith('.pdf')]
            
            total_size = 0
            for file in pdf_files:
                file_path = os.path.join(self.upload_dir, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
            
            return {
                'total_files': len(pdf_files),
                'total_size_mb': total_size / (1024 * 1024),
                'upload_directory': self.upload_dir
            }
            
        except Exception as e:
            logger.error(f"Failed to get upload stats: {e}")
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'upload_directory': self.upload_dir,
                'error': str(e)
            }

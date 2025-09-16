"""
Simplified FastAPI server for testing Gemini integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Agentic Research Assistant API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatPDFRequest(BaseModel):
    question: str
    paper_id: str = None

@app.get("/")
async def root():
    return {"message": "Agentic Research Assistant API", "status": "healthy"}

@app.post("/api/chat_pdf")
async def chat_pdf_endpoint(request: ChatPDFRequest):
    """Test endpoint to verify Gemini integration is working"""
    try:
        # Import here to avoid startup issues
        from agents.pdf_upload_handler import PDFUploadHandler
        
        # Find latest PDF
        pdf_dir = os.path.join(os.path.dirname(__file__), "uploads")
        if not os.path.isdir(pdf_dir):
            return {"answer": "No uploaded PDFs directory found on server."}

        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            return {"answer": "No PDF uploaded. Please upload a PDF first."}

        pdf_files_sorted = sorted(pdf_files, reverse=True)
        pdf_path = os.path.join(pdf_dir, pdf_files_sorted[0])
        
        logger.info(f"Using PDF: {pdf_path}")

        # Initialize handler with Google API key for Gemini
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            return {"answer": "Google API key not found. Please set GOOGLE_API_KEY in environment."}
            
        pdf_handler = PDFUploadHandler(
            upload_dir=pdf_dir,
            nebius_api_key=os.getenv("NEBIUS_API_KEY")  # Still needed for other agents
        )
        
        # Initialize the PDF analyzer and build FAISS index if needed
        await pdf_handler.pdf_analyzer.initialize_embeddings()
        
        # Check if we need to analyze the PDF (build FAISS index)
        if not hasattr(pdf_handler.pdf_analyzer, 'faiss_index') or pdf_handler.pdf_analyzer.faiss_index is None:
            logger.info(f"Building FAISS index for PDF: {pdf_path}")
            analysis_result = await pdf_handler.pdf_analyzer.analyze_pdf(pdf_path)
            logger.info(f"FAISS index built with {len(pdf_handler.pdf_analyzer.sentence_metadata)} sentences")
        
        # Check if analyzer exists and has index
        if not pdf_handler.pdf_analyzer:
            return {"answer": "PDF analyzer failed to initialize."}
            
        if not hasattr(pdf_handler.pdf_analyzer, 'faiss_index') or pdf_handler.pdf_analyzer.faiss_index is None:
            return {"answer": "Failed to build FAISS index from PDF."}

        # Test the ask_question method with Gemini integration
        logger.info(f"Calling ask_question with: {request.question}")
        result = await pdf_handler.pdf_analyzer.ask_question(request.question, top_k=8)
        
        logger.info(f"Gemini result: {result}")
        
        if result.get('answer'):
            return {
                "answer": result['answer'],
                "sources": result.get('sources', []),
                "context": result.get('context', ''),
                "gemini_called": True,
                "pdf_used": os.path.basename(pdf_path)
            }
        else:
            return {"answer": "No relevant information found in the uploaded PDF."}
            
    except Exception as e:
        logger.exception("Error in chat_pdf endpoint")
        return {"answer": f"Error: {str(e)}", "error_type": type(e).__name__}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
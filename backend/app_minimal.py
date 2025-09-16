from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from agents.pdf_upload_handler import PDFUploadHandler
import logging

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

# Global PDF handler
pdf_handler = None

class ChatPDFRequest(BaseModel):
    question: str
    paper_id: str = None

@app.get("/")
async def root():
    return {"message": "Agentic Research Assistant API", "status": "healthy"}

@app.post("/api/chat_pdf")
async def chat_pdf_endpoint(request: ChatPDFRequest):
    global pdf_handler
    
    try:
        # Initialize PDF handler if needed
        if not pdf_handler:
            nebius_api_key = os.getenv("NEBIUS_API_KEY")
            pdf_handler = PDFUploadHandler(
                upload_dir=os.path.join(os.path.dirname(__file__), "uploads"),
                nebius_api_key=nebius_api_key
            )
            logger.info("PDF handler initialized")

        # Find latest PDF
        pdf_dir = os.path.join(os.path.dirname(__file__), "uploads")
        if not os.path.isdir(pdf_dir):
            return {"answer": "No uploaded PDFs directory found on server."}

        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            return {"answer": "No PDF uploaded. Please upload a PDF first."}

        pdf_files_sorted = sorted(pdf_files, reverse=True)
        pdf_path = os.path.join(pdf_dir, pdf_files_sorted[0])

        # Check if analyzer is ready
        if not pdf_handler.pdf_analyzer:
            return {"answer": "PDF analyzer is not initialized. Please upload a PDF first."}

        # Use ask_question method for Gemini integration
        result = await pdf_handler.pdf_analyzer.ask_question(request.question, top_k=8)
        
        if result.get('answer'):
            return {
                "answer": result['answer'],
                "sources": result.get('sources', []),
                "context": result.get('context', '')
            }
        else:
            return {"answer": "No relevant information found in the uploaded PDF."}
            
    except Exception as e:
        logger.exception("Error in chat_pdf endpoint")
        return {"answer": f"Error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
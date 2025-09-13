<<<<<<< HEAD
# Agentic-Research-Assistant
a multi-agent system designed to streamline academic research by efficiently finding, summarizing, synthesizing, and presenting information from papers. This blueprint must include detailed specifications, architecture diagrams (described in text or Mermaid syntax), code skeletons 
=======
# Agentic Research Assistant

A multi-agent system designed to streamline academic research by efficiently finding, summarizing, synthesizing, and presenting information from papers.

## Architecture

\`\`\`mermaid
graph TB
    A[User Query] --> B[Search Agent]
    B --> C[Summary Agent]
    C --> D[Synthesizer Agent]
    D --> E[Voice Agent]
    D --> F[Monetization Agent]
    
    B --> G[(Academic APIs)]
    G --> H[arXiv]
    G --> I[Semantic Scholar]
    G --> J[OpenAlex]
    G --> K[GitHub]
    
    C --> L[Nebius AI Studio]
    D --> L
    E --> M[ElevenLabs API]
    F --> N[Crossmint API]
    
    O[PDF Upload] --> P[PDF Analysis Agent]
    P --> Q[Citation Mapping]
    P --> R[RAG Pipeline]
    
    S[Frontend Dashboard] --> T[WebSocket Updates]
    T --> U[Progress Tracking]
    T --> V[Real-time Results]
\`\`\`

## Features

### Multi-Agent System
- **Search Agent**: Concurrent queries across academic APIs
- **Summary Agent**: AI-powered paper summarization with relevance scoring
- **Synthesizer Agent**: Comprehensive report generation with gap analysis
- **Voice Agent**: Natural audio narration via ElevenLabs
- **Monetization Agent**: Payment processing and NFT minting

### PDF Analysis Integration
- Deep PDF parsing with citation mapping
- RAG pipeline for literature review generation
- Gaps and limitations detection with evidence linking

### Interactive Dashboard
- Real-time progress tracking via WebSockets
- Professional UI with tabbed results view
- Plagiarism checking and humanization scoring
- Audio player with waveform visualization

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### Environment Variables
Create `.env` file:
\`\`\`bash
NEBIUS_API_KEY=your_nebius_key
ELEVENLABS_API_KEY=your_elevenlabs_key
CROSSMINT_API_KEY=your_crossmint_key
NEXT_PUBLIC_API_URL=http://localhost:8000
\`\`\`

### Installation

1. **Clone and setup**:
\`\`\`bash
git clone <repository>
cd agentic-research-assistant
\`\`\`

2. **Start with Docker**:
\`\`\`bash
docker-compose up -d
\`\`\`

3. **Or run locally**:
\`\`\`bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app:app --reload

# Frontend
npm install
npm run dev
\`\`\`

### Usage

1. Open http://localhost:3000
2. Enter research query (e.g., "quantum computing ethics")
3. Monitor progress in real-time dashboard
4. Review summaries, synthesis, and gaps analysis
5. Listen to AI-generated audio narration
6. Export results or mint as NFT

## API Endpoints

- `POST /research` - Start research job
- `GET /status/{job_id}` - Get job progress
- `POST /rephrase` - Humanize/rephrase text
- `POST /plagiarism_check` - Check plagiarism risk

## Technology Stack

### Frontend
- Next.js 15 with App Router
- React 18 + TypeScript
- Tailwind CSS + shadcn/ui
- Framer Motion animations
- WebSocket real-time updates

### Backend
- FastAPI with async processing
- Celery for background tasks
- Redis for caching/queues
- PostgreSQL for data storage
- Coral Protocol for agent orchestration

### AI/ML
- Nebius AI Studio for LLM inference
- Sentence Transformers for embeddings
- FAISS for vector search
- PyMuPDF for PDF processing

### Integrations
- ElevenLabs for voice synthesis
- Crossmint for NFT minting
- Academic APIs (arXiv, Semantic Scholar, OpenAlex)

## Deployment

### Production Setup
1. Configure environment variables
2. Set up Vercel for frontend deployment
3. Deploy backend to Render/Heroku
4. Configure Redis and PostgreSQL instances
5. Set up monitoring and logging

### Security
- Rate limiting on API endpoints
- Input sanitization and validation
- JWT authentication for user sessions
- CORS configuration for production
- Zero-trust agent communication via Coral Protocol

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## License

MIT License - see LICENSE file for details
>>>>>>> a32c9f9 (Initial project upload)

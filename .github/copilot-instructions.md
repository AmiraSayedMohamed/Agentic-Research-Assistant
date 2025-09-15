# Copilot Instructions for Agentic Research Assistant

## Project Overview
This is a multi-agent system for academic research automation. It integrates a Next.js frontend with a FastAPI backend, orchestrating agents for search, summarization, synthesis, voice narration, monetization, and PDF analysis. Real-time updates are delivered via WebSockets.

## Architecture & Key Components
- **Frontend** (`app/`, `components/`): Next.js 15 (App Router), React 18, TypeScript, Tailwind CSS, shadcn/ui. Dashboard UI, PDF upload/view, authentication, and real-time progress.
- **Backend** (`backend/`): FastAPI app (`app.py`), agents in `backend/agents/` (e.g., `search_agent.py`, `summary_agent.py`). Uses Celery for async tasks, Redis for queues, PostgreSQL for storage.
- **Agents**: Each agent (search, summary, synthesizer, voice, monetization, PDF analysis) is a Python module in `backend/agents/`. Agents communicate via Coral Protocol and may call external APIs (arXiv, Semantic Scholar, OpenAlex, Nebius AI Studio, ElevenLabs, Crossmint).
- **PDF Analysis**: Deep parsing and citation mapping via `pdf_analysis_agent.py` and `pdf_upload_handler.py`.
- **WebSocket Updates**: Real-time job status and results pushed to frontend (`use-websocket.ts`, dashboard pages).

## Developer Workflows
- **Start All Services**: Use `docker-compose up -d` for full stack, or run backend (`uvicorn app:app --reload` in `backend/`) and frontend (`npm run dev`) separately.
- **Environment Variables**: Set API keys and URLs in `.env` (see README for required keys).
- **Testing**: Add tests for new features before submitting PRs. (Test files not present; follow FastAPI and Next.js conventions.)
- **API Endpoints**: Key endpoints in backend: `/research`, `/status/{job_id}`, `/rephrase`, `/plagiarism_check`.
- **Authentication**: JWT-based, with user store in `app/api/auth/userStore.ts`.

## Patterns & Conventions
- **Agent Modules**: Each agent is a self-contained Python class/function. Follow async patterns and use Celery for long-running jobs.
- **Frontend State**: Use React hooks (`hooks/`) for auth, toast, mobile, and WebSocket state.
- **UI Components**: Use shadcn/ui and Tailwind for consistent styling. Place reusable UI in `components/ui/`.
- **PDF Uploads**: Store in `public/uploads/` and process via backend agents.
- **Real-Time Updates**: Use WebSocket for job progress and results; see `use-websocket.ts` and dashboard pages.

## Integration Points
- **External APIs**: Academic search (arXiv, Semantic Scholar, OpenAlex), LLM inference (Nebius), voice (ElevenLabs), NFT minting (Crossmint).
- **Coral Protocol**: Used for agent orchestration and secure communication.
- **Celery/Redis**: For background task management and queueing.

## Examples
- To add a new agent: create a Python module in `backend/agents/`, register it in `app.py`, and update frontend to handle new results.
- To extend dashboard: add React components in `components/` and update state hooks in `hooks/`.

## References
- See `README.md` for setup, architecture diagram, and API details.
- Key files: `backend/app.py`, `backend/agents/`, `app/dashboard/`, `components/`, `hooks/`, `.env`.

---

If any section is unclear or missing, please provide feedback to improve these instructions.

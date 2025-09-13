# API Integration Guide - Agentic Research Assistant

This guide provides comprehensive information for integrating with the Agentic Research Assistant API.

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

Currently, the API operates in open mode for demonstration purposes. In production, implement authentication:

```python
# Example with API Key
headers = {
    "Authorization": "Bearer your-api-key",
    "Content-Type": "application/json"
}
```

## Core API Endpoints

### 1. System Information

#### GET /
Get basic system information and available agents.

```bash
curl -X GET "http://localhost:8000/"
```

**Response:**
```json
{
  "message": "Agentic Research Assistant API",
  "version": "1.0.0",
  "status": "active",
  "agents": [
    "Research Agent",
    "Summary Agent",
    "Synthesis Agent",
    "Presentation Agent"
  ]
}
```

#### GET /health
Health check endpoint for monitoring.

```bash
curl -X GET "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. Research Operations

#### POST /research
Conduct complete multi-agent research workflow.

```bash
curl -X POST "http://localhost:8000/research" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning bias detection",
    "max_papers": 15,
    "sources": ["arxiv", "crossref"],
    "include_preprints": true,
    "language": "en"
  }'
```

**Request Schema:**
```json
{
  "query": "string (required, 3-500 chars)",
  "max_papers": "integer (optional, 1-50, default: 10)",
  "date_range": {
    "start_date": "string (optional, YYYY-MM-DD)",
    "end_date": "string (optional, YYYY-MM-DD)"
  },
  "sources": ["string (optional, arxiv|pubmed|doaj|crossref)"],
  "include_preprints": "boolean (optional, default: true)",
  "language": "string (optional, default: en)"
}
```

## Client Libraries

### Python Client

```python
import requests
import json
from typing import Dict, Any, List

class ResearchAssistantClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def conduct_research(self, query: str, **kwargs) -> Dict[str, Any]:
        """Conduct complete research workflow"""
        payload = {"query": query, **kwargs}
        response = self.session.post(f"{self.base_url}/research", json=payload)
        response.raise_for_status()
        return response.json()
    
    def search_papers(self, query: str, max_papers: int = 10) -> List[Dict]:
        """Search for papers only"""
        payload = {"query": query, "max_papers": max_papers}
        response = self.session.post(f"{self.base_url}/search-papers", json=payload)
        response.raise_for_status()
        return response.json()["papers"]
    
    def get_history(self) -> List[Dict]:
        """Get research history"""
        response = self.session.get(f"{self.base_url}/research-history")
        response.raise_for_status()
        return response.json()["history"]

# Usage example
client = ResearchAssistantClient()
result = client.conduct_research(
    "climate change adaptation strategies",
    max_papers=20,
    sources=["crossref", "doaj"]
)
print(f"Found {len(result['papers_found'])} papers")
```

### JavaScript/Node.js Client

```javascript
class ResearchAssistantClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async conductResearch(query, options = {}) {
        const response = await fetch(`${this.baseUrl}/research`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, ...options })
        });
        
        if (!response.ok) {
            throw new Error(`Research failed: ${response.statusText}`);
        }
        
        return response.json();
    }
}

// Usage example
const client = new ResearchAssistantClient();
const result = await client.conductResearch(
    'artificial intelligence ethics',
    { max_papers: 15, include_preprints: false }
);
console.log(`Research completed in ${result.processing_time_seconds}s`);
```

## OpenAPI Specification

The complete API specification is available at:
- **Interactive Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`
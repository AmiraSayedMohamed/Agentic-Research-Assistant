# Deployment Guide - Agentic Research Assistant

This guide provides step-by-step instructions for deploying the Agentic Research Assistant in various environments.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- Git

## Quick Start with Docker Compose

### 1. Clone the Repository

```bash
git clone https://github.com/AmiraSayedMohamed/Agentic-Research-Assistant.git
cd Agentic-Research-Assistant
```

### 2. Environment Configuration

Create environment files for configuration:

```bash
# Backend environment (.env in root directory)
cat > .env << EOF
# API Keys (optional - demo mode works without)
OPENAI_API_KEY=your_openai_api_key_here

# Database
DATABASE_URL=sqlite:///./research_assistant.db

# Redis
REDIS_URL=redis://redis:6379

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
EOF

# Frontend environment
cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000
REACT_APP_APP_NAME=Agentic Research Assistant
EOF
```

### 3. Deploy with Docker Compose

```bash
# Build and start all services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Local Development Setup

### Backend Development

1. **Setup Python Environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Run Backend Server**
```bash
# Development mode with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using Python directly
python -m app.main
```

3. **Run Tests**
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx[test]

# Run tests
pytest tests/ -v
```

### Frontend Development

1. **Setup Node Environment**
```bash
cd frontend
npm install
```

2. **Run Development Server**
```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## Production Deployment

### Docker Production Setup

1. **Create Production Docker Compose**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - PYTHONPATH=/app
      - DATABASE_URL=sqlite:///./data/research_assistant.db
      - REDIS_URL=redis://redis:6379
    volumes:
      - research_data:/app/data
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - REACT_APP_API_URL=https://your-api-domain.com
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  research_data:
  redis_data:
```

2. **Deploy Production**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment Options

#### AWS ECS with Fargate

1. **Build and push images**
```bash
# Build images
docker build -t research-backend ./backend
docker build -t research-frontend ./frontend

# Tag for ECR
docker tag research-backend:latest 123456789012.dkr.ecr.region.amazonaws.com/research-backend:latest
docker tag research-frontend:latest 123456789012.dkr.ecr.region.amazonaws.com/research-frontend:latest

# Push to ECR
docker push 123456789012.dkr.ecr.region.amazonaws.com/research-backend:latest
docker push 123456789012.dkr.ecr.region.amazonaws.com/research-frontend:latest
```

2. **Create ECS Task Definition**
```json
{
  "family": "research-assistant",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "123456789012.dkr.ecr.region.amazonaws.com/research-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "sqlite:///./data/research_assistant.db"
        }
      ]
    }
  ]
}
```

#### Google Cloud Run

```bash
# Build and deploy backend
gcloud builds submit --tag gcr.io/PROJECT_ID/research-backend ./backend
gcloud run deploy research-backend --image gcr.io/PROJECT_ID/research-backend --platform managed --region us-central1

# Build and deploy frontend
gcloud builds submit --tag gcr.io/PROJECT_ID/research-frontend ./frontend
gcloud run deploy research-frontend --image gcr.io/PROJECT_ID/research-frontend --platform managed --region us-central1
```

#### Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: research-backend
  template:
    metadata:
      labels:
        app: research-backend
    spec:
      containers:
      - name: backend
        image: research-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "sqlite:///./data/research_assistant.db"
---
apiVersion: v1
kind: Service
metadata:
  name: research-backend-service
spec:
  selector:
    app: research-backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer
```

Deploy to Kubernetes:
```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
```

## Environment Variables

### Backend Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | None | No (demo mode) |
| `DATABASE_URL` | Database connection string | `sqlite:///./research_assistant.db` | No |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` | No |
| `API_HOST` | API host binding | `0.0.0.0` | No |
| `API_PORT` | API port | `8000` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Frontend Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REACT_APP_API_URL` | Backend API URL | `http://localhost:8000` | No |
| `REACT_APP_APP_NAME` | Application name | `Agentic Research Assistant` | No |

## Health Checks and Monitoring

### Health Check Endpoints

- **Backend Health**: `GET /health`
- **Backend Status**: `GET /`

### Monitoring Setup

1. **Prometheus Metrics** (optional)
```python
# Add to requirements.txt
prometheus-client==0.17.1

# Add to main.py
from prometheus_client import Counter, Histogram, generate_latest
```

2. **Docker Health Checks**
```bash
# Check container health
docker-compose ps
docker inspect --format='{{.State.Health.Status}}' container_name
```

## Troubleshooting

### Common Issues

1. **Backend fails to start**
   - Check Python dependencies: `pip install -r requirements.txt`
   - Verify environment variables
   - Check database permissions

2. **Frontend build fails**
   - Clear node modules: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility

3. **API connection errors**
   - Verify backend is running on correct port
   - Check CORS configuration
   - Verify network connectivity between containers

4. **Database issues**
   - Check file permissions for SQLite database
   - Verify database directory exists and is writable

### Logs and Debugging

```bash
# View application logs
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f

# Debug specific container
docker-compose exec backend bash
docker-compose exec frontend sh
```

## Security Considerations

1. **API Keys**: Store sensitive keys in environment variables or secrets manager
2. **HTTPS**: Use SSL certificates in production
3. **CORS**: Configure appropriate CORS settings for production domains
4. **Database**: Use proper database with authentication in production
5. **Rate Limiting**: Implement rate limiting for API endpoints

## Performance Optimization

1. **Caching**: Implement Redis caching for API responses
2. **Database**: Use PostgreSQL for better performance in production
3. **CDN**: Use CDN for frontend static assets
4. **Load Balancing**: Use multiple backend instances with load balancer

## Backup and Recovery

```bash
# Backup database
docker-compose exec backend sqlite3 /app/data/research_assistant.db ".backup /app/data/backup.db"

# Backup entire data volume
docker run --rm -v research_data:/data -v $(pwd):/backup alpine tar czf /backup/research_data.tar.gz /data
```
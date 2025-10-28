# ProdLens FastAPI Backend

REST API backend for the ProdLens AI development analytics dashboard. Bridges the Python-based ProdLens analytics engine with the React frontend dashboard.

## Overview

This FastAPI backend serves as the bridge between the existing ProdLens Python analytics modules and the React frontend dashboard. It provides:

- **REST API Endpoints**: Metrics, sessions, user profiles, and AI insights
- **Real-time WebSocket Updates**: Live metric and session data streaming
- **JWT Authentication**: Secure API access with token-based auth
- **CORS Support**: Frontend integration with localhost and custom domains
- **Observability**: Health checks and logging for monitoring

## Quick Start

### Prerequisites

- Python 3.11+
- pip or uv package manager

### Installation

```bash
# Clone and navigate to the api directory
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your configuration
```

### Running the Server

**Development Mode** (with hot reload):
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production Mode**:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or use the Makefile:
```bash
make dev      # Development server
make test     # Run tests
make docker-up  # Docker Compose
```

### Docker Deployment

**Build and run with Docker Compose:**
```bash
# Build image
make docker-build

# Start all services (API + LiteLLM + optional Phoenix)
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

Or manually:
```bash
docker-compose up -d
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Endpoints

### Health & Status
- `GET /` - API information
- `GET /health` - Health check with database status

### Authentication
- `POST /auth/token` - Get JWT access token
- `POST /auth/refresh` - Refresh access token

**Example:**
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'
```

### Metrics
- `GET /api/metrics` - Get aggregated metrics (7-day default)
- `GET /api/metrics/raw` - Get raw metrics data

**Query Parameters:**
- `since` (days): Number of days to include in metrics (default: 7)

### Sessions
- `GET /api/sessions` - List sessions with pagination and filters
- `GET /api/sessions/{session_id}` - Get session details

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `developer_id` (str): Filter by developer
- `model` (str): Filter by model name
- `sort_by` (str): Sort field (timestamp, cost_usd, tokens)
- `sort_order` (str): asc or desc

### Profile
- `GET /api/profile` - Get user profile and statistics

**Query Parameters:**
- `developer_id` (str): Get profile for specific developer

### Insights
- `GET /api/insights` - Get AI analytics insights and correlations

**Query Parameters:**
- `since` (days): Analysis window (default: 7)
- `lag_days` (int): Correlation lag (default: 1, max: 7)

### WebSocket (Real-time)
- `WS /ws/metrics` - Real-time metrics stream
- `WS /ws/sessions` - Real-time session updates

## Configuration

Configuration is managed via environment variables in `.env`:

```env
# Application
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
CORS_ALLOW_CREDENTIALS=true

# Database
DATABASE_URL=sqlite:///./cache.db
PRODLENS_CACHE_DB=.prod-lens/cache.db

# External Services
LITELLM_PROXY_URL=http://localhost:4000
GITHUB_TOKEN=your-github-token-here
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_metrics.py

# Run with verbose output
pytest -v
```

Test files:
- `tests/test_health.py` - Health check endpoints
- `tests/test_auth.py` - Authentication flow
- `tests/test_metrics.py` - Metrics endpoints
- `tests/test_sessions.py` - Session management
- `tests/test_profile.py` - User profiles
- `tests/test_insights.py` - Analytics insights
- `tests/test_cors.py` - CORS configuration

## Architecture

```
api/
├── main.py              # FastAPI application factory
├── config.py            # Configuration management
├── models.py            # Pydantic response models
├── auth.py              # JWT authentication utilities
├── database.py          # Database connections and ProdLens integration
├── routes/
│   ├── health.py        # Health check endpoints
│   ├── auth.py          # Authentication endpoints
│   ├── metrics.py       # Metrics endpoints
│   ├── sessions.py      # Session management endpoints
│   ├── profile.py       # User profile endpoints
│   ├── insights.py      # Analytics insights endpoints
│   └── websocket.py     # WebSocket handlers
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container image definition
├── docker-compose.yml   # Multi-service orchestration
├── pytest.ini           # Test configuration
└── Makefile             # Development commands
```

## Integration with ProdLens

The API seamlessly integrates with the existing ProdLens backend:

1. **Data Source**: Reads from `.prod-lens/cache.db` SQLite database
2. **Analytics**: Leverages `prodlens.metrics.ReportGenerator` for calculations
3. **Sessions**: Accesses normalized trace data from `prodlens.storage.ProdLensStore`
4. **GitHub Data**: Uses cached GitHub PR/commit data from ProdLens ETL

## Frontend Integration

The React dashboard connects via:

1. **API Base URL**: http://localhost:8000
2. **Authentication**: POST to `/auth/token` to get JWT token
3. **Headers**: Include `Authorization: Bearer <token>` in requests
4. **CORS**: Configured for localhost:5173 by default

**Example TypeScript client:**
```typescript
const client = new ApiClient('http://localhost:8000');

// Authenticate
const token = await client.authenticate('demo', 'demo123');

// Fetch metrics
const metrics = await client.getMetrics({ since: 7 });

// Stream real-time updates
const ws = new WebSocket('ws://localhost:8000/ws/metrics');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Metrics update:', update);
};
```

## Development

### Code Quality

Format and check code:
```bash
make format    # Black + isort
make lint      # Ruff linter
make type-check  # MyPy
```

### Database Inspection

```python
# Access ProdLens store directly
from database import get_prodlens_store

store = get_prodlens_store()
sessions = store.sessions_dataframe()
print(sessions.head())
```

## Deployment

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Kubernetes (Future)

Include Helm charts and kube manifests in `k8s/` directory (to be added).

### Environment-Specific Configs

- **Development**: `DEBUG=true`, hot reload enabled
- **Staging**: `DEBUG=false`, single worker, local Phoenix
- **Production**: `DEBUG=false`, 4+ workers, cloud Arize backend

## Troubleshooting

### Database Connection Error
```
Error connecting to cache.db: File not found
```
**Solution**: Ensure ProdLens has been run at least once to create the cache database:
```bash
cd dev-agent-lens/scripts
./main.py ingest-traces ../path/to/traces.jsonl
```

### CORS Error on Frontend
```
Access to XMLHttpRequest blocked by CORS policy
```
**Solution**: Update `CORS_ORIGINS` in `.env`:
```env
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### Authentication Token Expired
**Solution**: Token expires in 30 minutes by default. Refresh:
```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'
```

### WebSocket Connection Failed
**Solution**: Ensure WebSocket upgrade is supported. Check server logs and verify firewall rules allow WebSocket connections.

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and test: `make test`
3. Format code: `make format`
4. Commit with clear message
5. Submit pull request

## License

Same as parent repository.

## Support

- **Documentation**: See main README.md
- **Issues**: Report in repository issue tracker
- **Questions**: Check existing documentation and examples

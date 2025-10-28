# ProdLens API Backend - Quick Start Guide

Get the FastAPI backend running in 5 minutes!

## 1. Prerequisites

- Python 3.11+ installed
- 2GB+ free disk space
- Port 8000 available (or configure in .env)

## 2. Installation (2 minutes)

```bash
cd api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration
cp .env.example .env
```

## 3. Start the Server (1 minute)

```bash
# Option A: Development server (recommended for testing)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option B: Using Makefile
make dev

# Option C: Using Docker
docker-compose up -d
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 4. Test the API (2 minutes)

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Auth Token
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'

# Save token for next requests
export TOKEN="your-token-here"
```

### Fetch Metrics
```bash
curl http://localhost:8000/api/metrics
```

### List Sessions
```bash
curl http://localhost:8000/api/sessions
```

### Get Insights
```bash
curl http://localhost:8000/api/insights
```

## 5. Access Documentation

Open your browser:

- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **API Schema**: http://localhost:8000/openapi.json

## Available Commands

### Development

```bash
make dev          # Run development server with hot reload
make test         # Run all tests
make test-cov     # Run tests with coverage report
make lint         # Check code style
make format       # Format code
```

### Docker

```bash
make docker-build  # Build Docker image
make docker-up     # Start containers
make docker-down   # Stop containers
make docker-logs   # View logs
```

### Cleanup

```bash
make clean        # Remove cache and build artifacts
```

## Demo Credentials

Use these to test authentication:

| Username | Password  |
|----------|-----------|
| demo     | demo123   |
| pilot    | pilot123  |
| admin    | admin123  |

## API Endpoints

### Health & Status
- `GET /health` - Health check
- `GET /` - API info

### Authentication
- `POST /auth/token` - Get JWT token
- `POST /auth/refresh` - Refresh token

### Data Endpoints
- `GET /api/metrics` - Metrics (7-day default)
- `GET /api/sessions` - List sessions (paginated)
- `GET /api/sessions/{id}` - Session details
- `GET /api/profile` - User profile
- `GET /api/insights` - Analytics insights

### Real-time
- `WS /ws/metrics` - Metrics updates
- `WS /ws/sessions` - New session events

## Troubleshooting

### Port already in use
```bash
# Change port in .env
echo "API_PORT=8001" >> .env

# Or kill the process
lsof -i :8000  # Find process
kill -9 <PID>  # Kill it
```

### Database not found
```bash
# The app creates a test database automatically
# If needed, manually ensure ProdLens cache exists:
mkdir -p .prod-lens
touch .prod-lens/cache.db
```

### Import error for prodlens
```bash
# Ensure you're in the api directory
cd api

# And using the virtual environment
source venv/bin/activate
```

## Next Steps

1. **Run Tests**: `make test` - Verify everything works
2. **Read Docs**: Open http://localhost:8000/docs
3. **Check Data**: `GET /api/metrics` - Should return metrics
4. **Connect Frontend**: Update React app API_URL to http://localhost:8000
5. **WebSocket**: Try connecting to `ws://localhost:8000/ws/metrics`

## Common Queries

### Get metrics for last 30 days
```bash
curl "http://localhost:8000/api/metrics?since=30"
```

### List 10 sessions per page
```bash
curl "http://localhost:8000/api/sessions?page_size=10"
```

### Filter sessions by developer
```bash
curl "http://localhost:8000/api/sessions?developer_id=dev123"
```

### Get insights with custom lag
```bash
curl "http://localhost:8000/api/insights?lag_days=2"
```

### Authenticated request
```bash
TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/profile
```

## Environment Variables

Most important settings in `.env`:

```env
DEBUG=true              # Enable debug mode
API_PORT=8000          # Change port
JWT_SECRET_KEY=xxx     # Change in production
CORS_ORIGINS=[...]     # Add your frontend URL
```

## Need Help?

- **Documentation**: Read `README.md` for full guide
- **Deployment**: See `DEPLOYMENT.md` for production setup
- **Implementation**: Check `IMPLEMENTATION_SUMMARY.md` for details
- **API Docs**: Visit http://localhost:8000/docs (interactive)

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application |
| `config.py` | Environment configuration |
| `routes/*.py` | API endpoints |
| `tests/*.py` | Test suite |
| `.env.example` | Configuration template |
| `requirements.txt` | Python dependencies |
| `docker-compose.yml` | Container orchestration |
| `Makefile` | Common commands |

## What's Working

✅ Health checks
✅ JWT authentication
✅ Metrics API
✅ Sessions API
✅ Profile API
✅ Insights API
✅ WebSocket real-time
✅ CORS for frontend
✅ OpenAPI documentation
✅ Docker support
✅ Test suite
✅ Error handling

## What's Next

After basic testing:
1. Configure your frontend URL in CORS_ORIGINS
2. Integrate with React dashboard
3. Test WebSocket real-time updates
4. Set up Docker for deployment
5. Configure for production

---

**Need more info?** Check the full `README.md` or `DEPLOYMENT.md`.

Happy coding! 🚀

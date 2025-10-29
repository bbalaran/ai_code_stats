# ProdLens API Backend - Deployment Guide

This guide covers deploying the FastAPI backend in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Compose](#docker-compose)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Monitoring and Troubleshooting](#monitoring-and-troubleshooting)

## Local Development

### Quick Start

```bash
cd api

# Create environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points

- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Development Workflow

```bash
# In separate terminals:

# Terminal 1: API server (with hot reload)
make dev

# Terminal 2: Run tests while developing
watch pytest

# Terminal 3: Frontend development
cd ../dashboard/frontend
npm run dev
```

## Docker Compose

### Quick Start with Full Stack

```bash
cd api

# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Services Included

- **API** (prodlens-api): FastAPI backend on port 8000
- **LiteLLM Proxy** (litellm-proxy): Tracing proxy on port 4000
- **Phoenix** (optional): Local observability on port 6006

### Starting Specific Profiles

```bash
# With Phoenix (local observability)
docker-compose up -d --profile phoenix

# Without Phoenix
docker-compose up -d
```

### Environment Variables for Docker

Create `.env` in api directory:

```env
ENVIRONMENT=production
DEBUG=false
JWT_SECRET_KEY=your-production-secret-key
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
CORS_ORIGINS=["http://localhost:5173","http://yourdomain.com"]
```

### Container Health Monitoring

```bash
# Check container status
docker-compose ps

# View API health
curl http://localhost:8000/health

# View LiteLLM health
curl http://localhost:4000/health

# Check container logs
docker-compose logs api
docker-compose logs litellm
```

### Persistent Data

The configuration includes volumes:

```yaml
volumes:
  - ./.prod-lens:/app/.prod-lens      # ProdLens cache database
  - ./cache.db:/app/cache.db          # SQLite database
```

Data persists between container restarts.

## Production Deployment

### Pre-Deployment Checklist

- [ ] Database backed up
- [ ] Environment variables configured
- [ ] JWT secret key changed from default
- [ ] CORS origins updated for production domain
- [ ] SSL/TLS certificates obtained
- [ ] GitHub token configured
- [ ] Observability backend (Arize/Phoenix) configured
- [ ] Log aggregation setup

### Deployment Options

#### Option 1: Docker Container (Recommended)

```bash
# Build production image
docker build -t prodlens-api:v1.0.0 .

# Run container
docker run -d \
  --name prodlens-api \
  -p 8000:8000 \
  --env-file .env.production \
  -v /data/prodlens:/app/.prod-lens \
  -v /data/cache.db:/app/cache.db \
  --restart unless-stopped \
  prodlens-api:v1.0.0
```

#### Option 2: Kubernetes

Deploy using Helm charts (to be created):

```bash
helm install prodlens-api ./charts/api \
  -f values-production.yaml \
  --namespace prodlens
```

#### Option 3: Traditional Deployment

```bash
# On production server
cd /opt/prodlens-api

# Virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Systemd service
sudo cp prodlens-api.service /etc/systemd/system/
sudo systemctl enable prodlens-api
sudo systemctl start prodlens-api
```

**Systemd service file** (`prodlens-api.service`):

```ini
[Unit]
Description=ProdLens API Backend
After=network.target

[Service]
Type=notify
User=prodlens
WorkingDirectory=/opt/prodlens-api
EnvironmentFile=/opt/prodlens-api/.env.production
ExecStart=/opt/prodlens-api/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Reverse Proxy Setup

#### Nginx Configuration

```nginx
upstream prodlens_api {
    server localhost:8000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.prodlens.example.com;

    ssl_certificate /etc/ssl/certs/prodlens.crt;
    ssl_certificate_key /etc/ssl/private/prodlens.key;

    client_max_body_size 10M;

    location / {
        proxy_pass http://prodlens_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts for long-lived WebSocket connections
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # WebSocket-specific settings
    location /ws {
        proxy_pass http://prodlens_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
```

#### Apache Configuration

```apache
<VirtualHost *:443>
    ServerName api.prodlens.example.com

    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/prodlens.crt
    SSLCertificateKeyFile /etc/ssl/private/prodlens.key

    ProxyPreserveHost On
    ProxyRequests Off

    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/

    # WebSocket support
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) "ws://localhost:8000/$1" [P,L]
</VirtualHost>
```

### Database Migration

For production, consider migrating from SQLite to PostgreSQL:

```python
# Update DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost/prodlens_db
```

## Environment Configuration

### Required Variables

```env
# Application
ENVIRONMENT=production
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Security
JWT_SECRET_KEY=<generate-strong-random-key>
CORS_ORIGINS=["https://yourdomain.com"]

# Database
DATABASE_URL=sqlite:///./cache.db
PRODLENS_CACHE_DB=.prod-lens/cache.db

# APIs
GITHUB_TOKEN=ghp_<your-github-token>
ANTHROPIC_API_KEY=sk-ant-<your-key>
LITELLM_PROXY_URL=http://litellm:4000

# Observability
ARIZE_API_KEY=<optional-for-cloud>
ARIZE_SPACE_KEY=<optional-for-cloud>
```

### Generating JWT Secret

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Monitoring and Troubleshooting

### Health Checks

```bash
# API health
curl https://api.yourdomain.com/health

# Detailed status
curl https://api.yourdomain.com/health | jq

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "database_connected": true,
  "prodlens_cache_exists": true
}
```

### Logging

Logs are written to:
- **Docker**: `docker-compose logs api`
- **Systemd**: `journalctl -u prodlens-api -f`
- **File**: Configure in `.env` with `LOG_FILE=/var/log/prodlens-api.log`

### Performance Monitoring

```bash
# Monitor API response times
curl -w "@curl-format.txt" https://api.yourdomain.com/api/metrics

# Monitor database queries
curl https://api.yourdomain.com/health
```

### Debugging

Enable debug mode for troubleshooting:

```env
DEBUG=true
SQLALCHEMY_ECHO=true
```

**WARNING**: Never use DEBUG=true in production!

### Common Issues

**Issue**: Database file not found
```
ERROR: [Errno 2] No such file or directory: './.prod-lens/cache.db'
```

**Solution**: Run ProdLens once to create cache:
```bash
cd dev-agent-lens/scripts
python main.py ingest-traces traces.jsonl
```

**Issue**: CORS errors from frontend
```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution**: Update CORS_ORIGINS:
```env
CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com"]
```

**Issue**: WebSocket connection timeout
```
WebSocket connection failed
```

**Solution**:
1. Check firewall allows WebSocket (port 8000)
2. Verify reverse proxy WebSocket configuration
3. Increase proxy timeouts

## Backup and Recovery

### Database Backup

```bash
# SQLite backup
cp .prod-lens/cache.db .prod-lens/cache.db.backup.$(date +%Y%m%d)

# Automated daily backups
0 2 * * * cp /app/.prod-lens/cache.db /backups/cache.db.$(date +\%Y\%m\%d)
```

### Recovery

```bash
# Restore from backup
cp .prod-lens/cache.db.backup.20240101 .prod-lens/cache.db
```

## Scaling Considerations

### Horizontal Scaling

For high-traffic deployments:

1. **Load Balancer**: Use Nginx/HAProxy across multiple instances
2. **Shared Database**: Migrate from SQLite to PostgreSQL
3. **Session Management**: Use Redis for distributed sessions
4. **Cache Layer**: Add Redis for metrics caching

### Vertical Scaling

For single-server deployment:

```python
# Increase workers in uvicorn command
uvicorn main:app --workers 8 --worker-class uvicorn.workers.UvicornWorker
```

## Security Hardening

- [ ] Change JWT_SECRET_KEY to strong random value
- [ ] Enable HTTPS/SSL certificates
- [ ] Restrict CORS origins to trusted domains
- [ ] Use environment variables for all secrets (no .env in git)
- [ ] Enable authentication for all API endpoints
- [ ] Rate limiting on public endpoints
- [ ] Request validation and sanitization
- [ ] Regular security updates for dependencies

## Support and Updates

```bash
# Check for dependency updates
pip list --outdated

# Update all packages
pip install --upgrade -r requirements.txt

# Rebuild Docker image with latest dependencies
docker-compose build --no-cache
```

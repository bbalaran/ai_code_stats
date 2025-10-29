.PHONY: help install dev test lint format clean docker-build docker-up docker-down

help:
	@echo "ProdLens API Backend - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       Install dependencies"
	@echo "  make dev           Run development server"
	@echo "  make setup         Complete setup (install + copy .env)"
	@echo ""
	@echo "Development:"
	@echo "  make test          Run tests"
	@echo "  make test-cov      Run tests with coverage"
	@echo "  make lint          Run linter (ruff)"
	@echo "  make format        Format code (black, isort)"
	@echo "  make type-check    Run type checker (mypy)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build Docker image"
	@echo "  make docker-up     Start Docker containers"
	@echo "  make docker-down   Stop Docker containers"
	@echo "  make docker-logs   View Docker logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         Remove cache and build artifacts"

install:
	pip install -r requirements.txt

setup: install
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example - please configure"; fi

dev:
	python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term-missing

lint:
	ruff check .

format:
	isort .
	black .

type-check:
	mypy .

docker-build:
	docker build -t prodlens-api:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

docker-build-dev:
	docker build -f Dockerfile.dev -t prodlens-api:dev .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .coverage -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/

.DEFAULT_GOAL := help

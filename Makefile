.PHONY: help install test lint format docker-build docker-run docker-stop clean evaluate

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make evaluate      - Run evaluation tests"
	@echo "  make test          - Run unit tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code with black"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run with Docker Compose"
	@echo "  make docker-stop   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"
	@echo "  make run-local     - Run FastAPI locally"
	@echo "  make clean         - Clean up temporary files"

install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 pylint pytest-asyncio

evaluate:
	@echo "Running evaluation tests..."
	python evaluation.py

test:
	@echo "Running unit tests..."
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

lint:
	@echo "Running linters..."
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=__pycache__,venv,.env
	pylint multi_agent_system.py app.py evaluation.py --fail-under=7.0 || true

format:
	@echo "Formatting code..."
	black multi_agent_system.py app.py evaluation.py tests/

docker-build:
	@echo "Building Docker image..."
	docker build -t multi-agent-system:latest .

docker-run:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

run-local:
	@echo "Starting FastAPI locally..."
	uvicorn app:app --reload --host 0.0.0.0 --port 8000

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov
	@echo "Cleanup complete!"
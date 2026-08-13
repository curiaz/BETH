.PHONY: help install dev test lint format run migrate docker-up docker-down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	cd backend && pip install -e .

dev: ## Install development dependencies
	cd backend && pip install -e ".[dev]"

test: ## Run test suite with coverage
	cd backend && pytest -v --cov=app --cov-report=term-missing

test-unit: ## Run unit tests only
	cd backend && pytest tests/unit/ -v

test-integration: ## Run integration tests only
	cd backend && pytest tests/integration/ -v

test-api: ## Run API tests only
	cd backend && pytest tests/api/ -v

lint: ## Run linter
	cd backend && ruff check app/ tests/

format: ## Format code
	cd backend && ruff format app/ tests/

typecheck: ## Run type checker
	cd backend && mypy app/

run: ## Start the backend API server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create msg="description")
	cd backend && alembic revision --autogenerate -m "$(msg)"

docker-up: ## Start all services with Docker
	docker compose up --build -d

docker-down: ## Stop all Docker services
	docker compose down

docker-logs: ## Tail Docker logs
	docker compose logs -f

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -f backend/bethbot.db

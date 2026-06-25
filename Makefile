.PHONY: help install migrate test lint run worker

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install Python dependencies
	cd backend && pip install -r requirements.txt

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-init: ## Initialize Alembic migrations
	cd backend && alembic init migrations

migrate-revision: ## Create new migration
	cd backend && alembic revision --autogenerate -m "$(msg)"

run: ## Start the FastAPI development server
	cd backend && uvicorn app.main:app --reload --port 8000

worker: ## Start Celery worker
	cd backend && celery -A app.tasks.celery worker -l info -c 4

flower: ## Start Celery Flower monitoring
	cd backend && celery -A app.tasks.celery flower --port=5555

lint: ## Run linting (ruff/black)
	cd backend && ruff check . && black --check .

format: ## Format code (black/ruff)
	cd backend && black . && ruff check . --fix

test: ## Run pytest
	cd backend && pytest -xvs --tb=short

test-cov: ## Run tests with coverage
	cd backend && pytest --cov=app --cov-report=term-missing

compose-up: ## Start Docker Compose stack
	docker compose up -d --build

compose-down: ## Stop Docker Compose stack
	docker compose down -v

compose-logs: ## Tail Docker Compose logs
	docker compose logs -f

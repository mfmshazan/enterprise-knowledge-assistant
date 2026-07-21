# =============================================================================
# Enterprise Knowledge Assistant — developer task runner
# Run `make help` to see available targets.
# =============================================================================
.DEFAULT_GOAL := help
SHELL := /bin/sh

# ---------- Meta ----------
.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---------- Full stack (Docker) ----------
.PHONY: up down logs ps restart
up: ## Start the full stack (Postgres, Redis, Qdrant, MinIO, api, web)
	docker compose up -d --build

down: ## Stop the stack and remove containers
	docker compose down

logs: ## Tail logs from all services
	docker compose logs -f

ps: ## Show running services
	docker compose ps

restart: down up ## Restart the full stack

# ---------- Backend ----------
.PHONY: be-install be-dev be-test be-lint be-format be-typecheck
be-install: ## Install backend deps with uv
	cd backend && uv sync

be-dev: ## Run the API locally with reload
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

be-test: ## Run backend tests
	cd backend && uv run pytest -q

be-lint: ## Lint backend with ruff
	cd backend && uv run ruff check .

be-format: ## Auto-format backend with ruff
	cd backend && uv run ruff format .

be-typecheck: ## Type-check backend with mypy
	cd backend && uv run mypy app

# ---------- Frontend ----------
.PHONY: fe-install fe-dev fe-build fe-lint
fe-install: ## Install frontend deps
	cd frontend && npm install

fe-dev: ## Run the Next.js dev server
	cd frontend && npm run dev

fe-build: ## Production build of the frontend
	cd frontend && npm run build

fe-lint: ## Lint the frontend
	cd frontend && npm run lint

# ---------- Quality gate (what CI runs) ----------
.PHONY: check
check: be-lint be-typecheck be-test fe-lint ## Run the full quality gate

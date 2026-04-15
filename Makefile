# Panther Cloud Air (PCA) Makefile
# CSC 4710 Spring 2026 | ctrlC+ctrlV

.PHONY: all setup start stop restart build logs clean frontend backend db help

## Default target
all: help

## Setup

setup: ## Install all dependencies (run once)
	@echo "==> Setting up frontend dependencies..."
	cd frontend && npm install
	@echo "==> Building Docker images..."
	docker compose build --no-cache
	@echo "==> Setup complete. Run 'make start' to launch."

## Run

start: ## Start all services (frontend, backend, database)
	docker compose up -d
	@echo "==> PCA is running:"
	@echo "    Frontend : http://localhost:3000"
	@echo "    Backend  : http://localhost:5001/api/health"
	@echo "    Database : internal (Docker network only)"

stop: ## Stop all services
	docker compose down

restart: stop start ## Restart all services

## Development

dev-frontend: ## Run frontend in dev mode (no Docker)
	cd frontend && npm run dev

dev-backend: ## Run backend in dev mode (no Docker; needs DB running)
	cd backend && python run.py

## Database

db: ## Start only the database
	docker compose up -d db

db-shell: ## Open MariaDB shell
	docker exec -it pca_db mariadb -u pca_user -ppca_password pca_db

db-reset: ## Drop and recreate the database (WARNING: destroys data)
	docker compose down -v
	docker compose up -d db
	@echo "==> Database reset. Run 'make start' to restart all services."

## Logs

logs: ## Show logs for all services
	docker compose logs -f

logs-backend: ## Show backend logs only
	docker compose logs -f backend

logs-db: ## Show database logs only
	docker compose logs -f db

## Utilities

build: ## Rebuild Docker images from scratch
	docker compose build --no-cache

clean: ## Remove containers and volumes (keeps images)
	docker compose down -v --remove-orphans

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

.PHONY: help build up down logs shell test lint format clean

help:
	@echo "Available commands:"
	@echo "  build     - Build Docker images"
	@echo "  up        - Start all services"
	@echo "  down      - Stop all services"
	@echo "  logs      - Show logs"
	@echo "  shell     - Open API shell"
	@echo "  test      - Run tests"
	@echo "  lint      - Run linting"
	@echo "  format    - Format code"
	@echo "  clean     - Clean up Docker resources"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

shell:
	docker-compose exec api bash

test:
	docker-compose exec api pytest tests/ -v

lint:
	docker-compose exec api flake8 app/
	docker-compose exec api mypy app/

format:
	docker-compose exec api black app/
	docker-compose exec api isort app/

clean:
	docker-compose down -v
	docker system prune -f

# Database migrations
migrate:
	docker-compose exec api alembic upgrade head

migration:
	docker-compose exec api alembic revision --autogenerate -m "$(MSG)"

# Development shortcuts
dev-setup:
	cp .env.example .env
	@echo "Please edit .env with your configuration"

dev-run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	celery -A app.tasks.celery_app worker --loglevel=info

beat:
	celery -A app.tasks.celery_app beat --loglevel=info

flower:
	celery -A app.tasks.celery_app flower --port=5555

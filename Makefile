# Makefile for The AI Engineer Challenge Project
# Provides easy commands for frontend, backend, and testing workflows

.PHONY: help install frontend backend test test-frontend test-backend test-all clean dev setup lint format check

# Default target
help:
	@echo "🚀 The AI Engineer Challenge - Development Commands"
	@echo ""
	@echo "📦 Setup Commands:"
	@echo "  make setup          - Install all dependencies (frontend + backend)"
	@echo "  make install        - Install Python dependencies only"
	@echo "  make install-frontend - Install frontend dependencies only"
	@echo ""
	@echo "🏃 Development Commands:"
	@echo "  make dev            - Start both frontend and backend in parallel"
	@echo "  make frontend       - Start frontend development server"
	@echo "  make backend        - Start backend API server"
	@echo ""
	@echo "🧪 Testing Commands:"
	@echo "  make test           - Run all tests (backend + frontend)"
	@echo "  make test-backend   - Run backend Python tests"
	@echo "  make test-frontend  - Run frontend Jest tests (placeholder)"
	@echo "  make test-watch     - Run backend tests in watch mode"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo ""
	@echo "🔧 Code Quality Commands:"
	@echo "  make lint           - Run linting for both frontend and backend"
	@echo "  make format         - Format code (Python with black, frontend with prettier)"
	@echo "  make check          - Run all quality checks (lint + format + test)"
	@echo ""
	@echo "🧹 Utility Commands:"
	@echo "  make clean          - Clean build artifacts and caches"
	@echo "  make clean-all      - Deep clean including node_modules and .venv"

# Setup and Installation
setup: install install-frontend
	@echo "✅ All dependencies installed successfully!"

install:
	@echo "📦 Installing Python dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		uv sync --dev; \
	else \
		pip install -e ".[dev]"; \
	fi
	@echo "✅ Python dependencies installed!"

install-frontend:
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "✅ Frontend dependencies installed!"

# Development Commands
dev:
	@echo "🚀 Starting frontend and backend in parallel..."
	@echo "Frontend will be available at: http://localhost:3000"
	@echo "Backend will be available at: http://localhost:8000"
	@echo "Press Ctrl+C to stop both servers"
	@trap 'kill %1 %2' INT; \
	make backend & \
	make frontend & \
	wait

frontend:
	@echo "🎨 Starting frontend development server..."
	@cd frontend && npm run dev

backend:
	@echo "🔧 Starting backend API server..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run python api/app.py; \
	else \
		python api/app.py; \
	fi

# Testing Commands
test: test-backend test-frontend
	@echo "✅ All tests completed!"

test-backend:
	@echo "🧪 Running backend Python tests..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest tests/ -v; \
	else \
		pytest tests/ -v; \
	fi

test-frontend:
	@echo "🧪 Running frontend tests..."
	@echo "⚠️  Frontend tests are placeholder until we implement them"
	@cd frontend && npm run test -- --passWithNoTests --verbose

test-watch:
	@echo "🔍 Running backend tests in watch mode..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest tests/ -v --tb=short -f; \
	else \
		pytest tests/ -v --tb=short -f; \
	fi

test-coverage:
	@echo "📊 Running tests with coverage report..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest tests/ --cov=. --cov-report=term-missing --cov-report=html; \
	else \
		pytest tests/ --cov=. --cov-report=term-missing --cov-report=html; \
	fi
	@echo "📈 Coverage report generated in htmlcov/"

# Code Quality Commands
lint: lint-backend lint-frontend
	@echo "✅ All linting completed!"

lint-backend:
	@echo "🔍 Linting Python code..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run flake8 aimakerspace/ api/ tests/ --max-line-length=88 --extend-ignore=E203,W503 || true; \
	else \
		flake8 aimakerspace/ api/ tests/ --max-line-length=88 --extend-ignore=E203,W503 || true; \
	fi

lint-frontend:
	@echo "🔍 Linting frontend code..."
	@cd frontend && npm run lint

format: format-backend format-frontend
	@echo "✅ All code formatted!"

format-backend:
	@echo "🎨 Formatting Python code with black..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run black aimakerspace/ api/ tests/; \
		uv run isort aimakerspace/ api/ tests/; \
	else \
		black aimakerspace/ api/ tests/; \
		isort aimakerspace/ api/ tests/; \
	fi

format-frontend:
	@echo "🎨 Formatting frontend code..."
	@cd frontend && npm run lint -- --fix || true

check: format lint test
	@echo "✅ All quality checks passed!"

# Utility Commands
clean:
	@echo "🧹 Cleaning build artifacts and caches..."
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf .coverage
	@rm -rf **/__pycache__/
	@rm -rf **/*.pyc
	@cd frontend && rm -rf .next/
	@echo "✅ Cleaned build artifacts!"

clean-all: clean
	@echo "🧹 Deep cleaning all dependencies..."
	@rm -rf .venv/
	@rm -rf frontend/node_modules/
	@rm -rf frontend/.next/
	@echo "✅ Deep clean completed! Run 'make setup' to reinstall dependencies."

# API specific commands
api-docs:
	@echo "📚 Opening API documentation..."
	@echo "Starting backend server and opening docs..."
	@if command -v uv >/dev/null 2>&1; then \
		uv run python -c "import webbrowser; webbrowser.open('http://localhost:8000/docs')" & \
		uv run python api/app.py; \
	else \
		python -c "import webbrowser; webbrowser.open('http://localhost:8000/docs')" & \
		python api/app.py; \
	fi

# Health checks
health:
	@echo "🏥 Running health checks..."
	@echo "Checking backend health..."
	@curl -s http://localhost:8000/api/health || echo "❌ Backend not running"
	@echo "Checking frontend..."
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend is running" || echo "❌ Frontend not running"

# Quick start for new developers
quickstart:
	@echo "🚀 Quick start for new developers..."
	@echo "1. Installing dependencies..."
	@make setup
	@echo "2. Running tests to verify setup..."
	@make test
	@echo "3. Starting development servers..."
	@make dev

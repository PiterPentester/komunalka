# Variables
APP_NAME := komunalka
IMAGE_TAG := latest
DOCKER_IMAGE := $(APP_NAME):$(IMAGE_TAG)
PYTHON := python3
PIP := pip
PYTEST := pytest

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make dev          - Run development server with uv"
	@echo "  make install      - Install local dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run ruff linter"
	@echo "  make format       - Format code with ruff"
	@echo "  make check-format - Check code formatting with ruff"
	@echo "  make clean        - Remove caches and temporary files"
	@echo "  make docker-build - Build Chainguard-based Docker image"
	@echo "  make docker-run   - Run the application in Docker"
	@echo "  make k8s-deploy   - Deploy to Kubernetes using Kustomize"
	@echo "  make k8s-status   - Check status of K8s deployment"

# Local Development
.PHONY: install
install:
	uv sync

.PHONY: dev
dev:
	uv run uvicorn app:app --reload

.PHONY: test
test:
	PYTHONPATH=. uv run $(PYTEST) tests/

.PHONY: lint
lint:
	uvx ruff check .

.PHONY: format
format:
	uvx ruff format .

.PHONY: check-format
check-format:
	uvx ruff format --check .

.PHONY: clean
clean:
	rm -rf .pytest_cache .ruff_cache __pycache__ .venv .uv
	find . -type d -name "__pycache__" -exec rm -rf {} +

# Docker operations
.PHONY: docker-build
docker-build:
	docker build -t $(DOCKER_IMAGE) .

.PHONY: docker-arm64-build
docker-arm64-build:
	docker buildx build --platform linux/arm64 -t $(DOCKER_IMAGE) .

.PHONY: docker-run
docker-run:
	docker run -p 8000:8000 --env-file .env $(DOCKER_IMAGE)

# Kubernetes operations
.PHONY: k8s-deploy
k8s-deploy:
	kubectl apply -f k8s/

.PHONY: k8s-status
k8s-status:
	kubectl get pods,svc,pvc,deployment -l app=komunalka
	kubectl logs deployment/komunalka --tail=50

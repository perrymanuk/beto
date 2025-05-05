.PHONY: run install test lint format docker-build docker-up docker-down

# Run the API locally
run:
	uvicorn app.main:app --reload

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests (to be implemented)
test:
	echo "No tests implemented yet"

# Lint the code
lint:
	black app
	isort app

# Format the code
format:
	black app
	isort app

# Build Docker image
docker-build:
	docker-compose build

# Start Docker containers
docker-up:
	docker-compose up -d

# Stop Docker containers
docker-down:
	docker-compose down
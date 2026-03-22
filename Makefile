.PHONY: up down reset-db load all

# Start containers
up:
	docker compose up -d --build
	@echo "FastAPI is running at: http://localhost:8000"

# Stop containers
down:
	docker compose down

# Reset DB completely
reset-db:
	docker compose down -v
	docker compose up -d

# Load data into DB
load:
	python3 DATA/load_to_db.py

# Wait for DB to be ready
wait-db:
	@echo "Waiting for database to start..."
	docker compose exec db sh -c "until pg_isready -U postgres; do sleep 1; done"
	@echo "Database is ready."

all: up wait-db load
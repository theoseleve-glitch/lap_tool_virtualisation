.PHONY: up down migrate test lint

up:
	docker compose up -d --build

down:
	docker compose down -v

migrate:
	psql postgresql://trackreco:trackreco@localhost:5432/trackreco -f migrations/0001_initial.sql

test:
	pytest -q

lint:
	python -m compileall src

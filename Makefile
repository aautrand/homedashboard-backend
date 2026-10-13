# use bash so read -p works reliably
SHELL := /bin/bash

# Settings and secrets live outside the repo; nothing here loads a .env file.
ENV_FILE ?= $(HOME)/.config/homedashboard/env
WITH_ENV = set -a; . $(ENV_FILE); set +a;

build:
	docker compose build

run:
	docker compose up

format:
	black .
	isort .

format-check:
	black --check --diff .
	isort --check --diff .

lint:
	ruff check .

test:
	python -m pytest tests/ -v

security:
	bandit -c bandit.yaml -r dashboard/

check: format-check lint-fix test security

push: check
	git push --set-upstream origin $(shell git rev-parse --abbrev-ref HEAD)

lint-fix:
	ruff check --fix .

# Run the app the way production does, with settings from ENV_FILE.
serve:
	$(WITH_ENV) gunicorn --bind 0.0.0.0:8050 --timeout 180 app:app

# Apply database migrations against the database named in ENV_FILE.
migrate:
	$(WITH_ENV) alembic upgrade head

# Turn on the pre-push secret scan in .githooks/ (needs gitleaks).
hooks:
	git config core.hooksPath .githooks

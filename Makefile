# use bash so read -p works reliably
SHELL := /bin/bash

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

# Turn on the pre-push secret scan in .githooks/ (needs gitleaks).
hooks:
	git config core.hooksPath .githooks

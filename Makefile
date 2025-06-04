build:
	docker compose build

run:
	docker compose up

format:
	isort .
	black .

format-check:
	isort --check --diff .
	black --check --diff .
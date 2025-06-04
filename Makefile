build:
	docker compose build

run:
	docker compose up

format:
	isort .
	black .

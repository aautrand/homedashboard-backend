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

test:
	python -m pytest tests/ -v


# tweak these to taste
VERSION_FILE := version
IMAGE        := localhost:5000/homedashboard-be

push-image:
	@set -euo pipefail; \
	current=$$(cat $(VERSION_FILE)); \
	echo "Current version: $$current"; \
	read -p "Enter new version: " new_ver; \
	read -p "You entered '$$new_ver'. Proceed with push? [y/N]: " confirm; \
	if [[ "$$confirm" != [yY] ]]; then echo "Aborted."; exit 1; fi; \
	echo $$new_ver > $(VERSION_FILE); \
	git add $(VERSION_FILE); \
	git commit -m "[system] Bump version to $$new_ver"; \
	podman build -t $(IMAGE):$$new_ver .; \
	podman push $(IMAGE):$$new_ver; \
	scp .env ganymede:/home/aautrand/homedashboard-be/.env

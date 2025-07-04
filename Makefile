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

push-image:
	docker build -t localhost:5000/homedashboard-be:latest .
	docker push localhost:5000/homedashboard-be:latest
	scp .env mainserver:/home/aautrand/homedashboard-be/.env

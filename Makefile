up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

format:
	poetry run black .
	poetry run isort .

test:
	poetry run pytest
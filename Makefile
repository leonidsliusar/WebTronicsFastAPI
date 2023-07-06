run_app:
	docker compose up -d

stop_app:
	docker compose down -v

test:
	pip install poetry && poetry install --no-interaction && poetry update && pytest -vv
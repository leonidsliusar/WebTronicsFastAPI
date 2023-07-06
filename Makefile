run_app:
	docker compose up -d

stop_app:
	docker compose down -v

test:
	pip install poetry && \
    poetry install --no-interaction && \
    export DB_LOGIN=postgres && \
    export DB_PASSWORD=postgres && \
    export DB_NAME=social_net && \
    export DB_PORT=5450 && \
    export DB_HOST=localhost && \
    export DB_TEST_PORT=5451 && \
    export REFRESH_TOKEN_EXPIRES_IN=10080 && \
    export ACCESS_TOKEN_EXPIRES_IN=15 && \
    export ALGORITHM=HS256 && \
    export SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7 && \
    export REDIS_PORT=6379 && \
    export REDIS_HOST=localhost && \
    poetry update && \
    pytest -vv

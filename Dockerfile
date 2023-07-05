FROM python:3.10-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
RUN pip install poetry

COPY pyproject.toml /app/pyproject.toml
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-dev
RUN poetry update
COPY . /app

EXPOSE 8000
CMD alembic upgrade head && python main.py
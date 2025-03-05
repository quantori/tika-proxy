FROM python:3-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY . .

RUN uv sync --frozen --no-cache

CMD [ "/app/.venv/bin/python3", "main.py" ]
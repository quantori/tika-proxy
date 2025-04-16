FROM python:3-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup appuser

RUN chown -R appuser:appgroup /app

COPY --chown=appuser:appgroup . .

USER appuser

RUN uv sync --frozen --no-cache

CMD [ "/app/.venv/bin/python3", "main.py" ]
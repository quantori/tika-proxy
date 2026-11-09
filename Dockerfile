# 3.13: uv.lock pins pydantic-core 2.27.2, which has no wheels for 3.14 (python:3-slim
# moved to 3.14 and the build then needs a Rust toolchain).
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup appuser

RUN chown -R appuser:appgroup /app

COPY --chown=appuser:appgroup . .

USER appuser

RUN uv sync --frozen --no-cache

CMD [ "/app/.venv/bin/python3", "main.py" ]
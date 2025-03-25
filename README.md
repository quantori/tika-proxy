# Tika proxy

This is a proxy for Apache Tika that splits large documents into pages for parallel processing. You can configure it using environment variables. Adjust the TIKA_CHUNK value for better performance.

## Setup

Environment vars:

HOST - Listen host (0.0.0.0)

PORT - Listen port (9010)

TIKA_URL - Tika endpoint: (http://localhost:9099)

TIKA_CHUNK - Tika parallel batch size (8)

## Run

```
uv sync

. .venv/bin/activate

python3 main.py
```

## Docker & docker-compose

```
docker run docker pull ghcr.io/quantori/tika-proxy:latest
```

```(yaml)
tika-proxy:
  image: ghcr.io/quantori/tika-proxy:latest
  environment:
    - TIKA_CHUNK=120
    - TIKA_URL=http://tika:9998
  restart: always
```

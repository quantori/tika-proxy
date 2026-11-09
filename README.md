# Tika proxy

This is a proxy for Apache Tika that splits PDF documents into pages for parallel processing. You can configure it using environment variables. Adjust the TIKA_CHUNK value for better performance.

## Behaviour

- A request is treated as a PDF when its body starts with `%PDF-`, or when `Content-Type: application/pdf` is set. The content check comes first: Open WebUI (0.6.35 and later) sends no `Content-Type`, and browsers often send a wrong one.
- A PDF is split into single pages, which are sent to Tika `TIKA_CHUNK` at a time. The texts are concatenated in page order; the metadata of the first page stands in for the document's.
- A PDF that cannot be split (encrypted with a user password, malformed) is sent to Tika whole, as a single request. Everything that is not a PDF is also sent whole.
- A page that fails (connection error, non-200, bad JSON) is retried once after `TIKA_RETRY_DELAY` seconds, which covers a Tika worker restart. If it fails again the page is skipped and logged as an error; the text is assembled from the other pages.
- The request fails with HTTP 502 only when not a single page could be parsed, that is when Tika is down or rejects everything.
- If the client disconnects while a document is being processed (for example a proxy in front of this one timed out), the remaining pages are not sent to Tika.
- Tika's HTTP status is passed through. An unreachable Tika gives HTTP 502.

## Setup

Environment vars:

HOST - Listen host (0.0.0.0)

PORT - Listen port (9010)

TIKA_URL - Tika endpoint: (http://localhost:9998)

TIKA_CHUNK - Tika parallel batch size (8)

TIKA_RETRY_DELAY - Seconds to wait before retrying a failed page (3)

## Run

```
uv sync --python 3.13

. .venv/bin/activate

python3 main.py
```

## Docker & docker-compose

```
docker pull ghcr.io/quantori/tika-proxy:latest
```

```(yaml)
tika-proxy:
  image: ghcr.io/quantori/tika-proxy:latest
  environment:
    - TIKA_CHUNK=120
    - TIKA_URL=http://tika:9998
  restart: always
```

`latest` follows the `main` branch. Releases are published from git tags: pushing a tag
such as `v0.0.2` also publishes the image as `ghcr.io/quantori/tika-proxy:v0.0.2` and
`ghcr.io/quantori/tika-proxy:0.0.2`. Every build is additionally tagged with the short
commit SHA.

# Tika proxy


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


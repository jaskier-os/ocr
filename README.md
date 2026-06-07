# OCR Microservice

A small FastAPI HTTP service that performs optical character recognition on images
using the LightOnOCR vision-language model (via HuggingFace `transformers`). It exposes
a single `/ocr` endpoint that accepts a base64-encoded image and returns the extracted
text plus the image dimensions. Authentication is a static Bearer API key.

## Prerequisites

- Python 3.12
- Roughly 4-8 GB of free disk for the model weights (downloaded on first run)
- Optional: an NVIDIA GPU with CUDA for faster inference (`DEVICE=cuda`)

## Setup

1. Copy the example environment file and fill in the values:

   ```bash
   cp .env.example .env
   ```

   Environment variables (all read by `config.py`):

   | Variable         | Default                       | Description                                                        |
   | ---------------- | ----------------------------- | ------------------------------------------------------------------ |
   | `MODEL_ID`       | `lightonai/LightOnOCR-2-1B`   | HuggingFace model id, auto-downloaded on first run.                |
   | `DEVICE`         | `cpu`                         | Inference device: `cpu` or `cuda`.                                 |
   | `DTYPE`          | `float32`                     | Torch dtype: `float32`, `float16`, `bfloat16` (forced to `float32` on CPU). |
   | `MAX_NEW_TOKENS` | `4096`                        | Max tokens generated per OCR request.                              |
   | `PORT`           | `10006`                       | HTTP listen port.                                                  |
   | `API_KEY`        | (required, no default)        | Bearer token clients must send in the `Authorization` header.      |

   `API_KEY` is mandatory; the service refuses to start without it.

## Build / Install

Using the helper script (creates a local venv and installs pinned deps):

```bash
./run.sh
```

Or manually:

```bash
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
venv/bin/python main.py
```

## Run

```bash
./run.sh
```

The service starts on `http://0.0.0.0:<PORT>` (default `10006`).

Health check:

```bash
curl http://localhost:10006/health
```

OCR request:

```bash
curl -X POST http://localhost:10006/ocr \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"image_base64\": \"<base64-encoded-image>\"}"
```

Response:

```json
{ "text": "...extracted text...", "width": 1024, "height": 768 }
```

## Docker

```bash
docker build -t ocr .
docker run --rm -p 10006:10006 --env-file .env ocr
```

The provided `Dockerfile` installs the CPU build of torch. For GPU, adjust the torch
install line and run with `--gpus all` and `DEVICE=cuda`.

## Tests

An end-to-end test script exercises the running service:

```bash
# Start the service first, then in another shell:
venv/bin/python test_e2e.py --image /path/to/test-image.png
venv/bin/python test_e2e.py --url http://localhost:10006 --image /path/to/test-image.png
```

The test checks the health endpoint, auth rejection, bad-image handling, and a full OCR
pass. The default expected-words assertion targets a sample Russian store receipt; pass
your own `--image` and adjust as needed.

## Model weights

`MODEL_ID` points at a standard pretrained model published on HuggingFace
(`lightonai/LightOnOCR-2-1B`). It is **not** bundled in this repository; `transformers`
downloads and caches it automatically on first startup (into the HuggingFace cache,
typically `~/.cache/huggingface`). No manual fetch step is required. To use a different
model, set `MODEL_ID` to any compatible LightOnOCR checkpoint.

## TLS / VPN

This service speaks plain HTTP and does not require any certificate or VPN. If you need
TLS, terminate it at a reverse proxy (nginx, Caddy, Traefik) in front of the service.

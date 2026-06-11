# ocr

> **Docs & wiki:** [github.com/jaskier-os/docs/wiki](https://github.com/jaskier-os/docs/wiki)

## What it is

An OCR HTTP service. Send it an image, it runs the LightOnOCR vision model
(`lightonai/LightOnOCR-2-1B` via transformers) and returns the extracted text.
FastAPI, port 10006. `POST /ocr` (bearer-token auth), `GET /health`.

## Build / run

Local:

```bash
cp .env.example .env   # set API_KEY, pick DEVICE
./run.sh               # creates venv, installs requirements, starts main.py
```

Or by hand:

```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt
venv/bin/python main.py
```

The model is pulled from HuggingFace by transformers on first run (no separate
fetch step), so the first start is slow - the Docker healthcheck allows a 120s
start period for this.

Docker (CPU torch wheel baked in):

```bash
docker build -t ocr .
docker run -p 10006:10006 --env-file .env ocr
```

For GPU set `DEVICE=cuda` and `DTYPE=float16`/`bfloat16`, and use a CUDA-enabled
torch instead of the CPU wheel the Dockerfile installs.

## Configuration

Config is env vars. `.env.example` is the source of truth - copy to `.env` and
edit. What matters:

- `API_KEY` - bearer token required on `/ocr`.
- `MODEL_ID` - HuggingFace model id (default `lightonai/LightOnOCR-2-1B`).
- `DEVICE` - `cpu` or `cuda`.
- `DTYPE` - `float32` / `float16` / `bfloat16` (forced to float32 on cpu).
- `MAX_NEW_TOKENS`, `PORT`.

## Dependencies

Python 3.12, FastAPI + uvicorn, `transformers`, `torch`, `pillow`,
`sentencepiece`, `accelerate`. The Dockerfile installs the CPU torch wheel from
the PyTorch index; the OCR weights download at runtime, not at build time.

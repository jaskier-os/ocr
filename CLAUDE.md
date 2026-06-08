# CLAUDE.md -- OCR Service

This file provides guidance to Claude Code when working in this repository.

IMPORTANT: NEVER USE EMOJIS ANYWHERE IN LOGGING, CODE OR OTHER TEXT.

IMPORTANT: Treat this codebase as work in progress. Never do backwards-compatibility or legacy support unless explicitly asked. Remove code that becomes redundant.

## What this service is

An OCR microservice for extracting text from images. It runs the LightOnOCR vision-language
model (`lightonai/LightOnOCR-2-1B` by default) via HuggingFace transformers behind a FastAPI
HTTP API. It is the OCR backend for the AI orchestration system.

This service listens on **port 10006**.

For the whole-system architecture and the full port table, see the orchestrator repo
(`jaskier-os/orchestrator`) CLAUDE.md / docs -- do not duplicate that map here.

## Tech stack

- Python 3 + FastAPI
- HuggingFace transformers + torch (model auto-downloaded on first run)
- CPU or CUDA (`DEVICE`, `DTYPE`)

## Run

```bash
bash run.sh    # creates venv, installs requirements.txt, runs main.py
```

Copy `.env.example` to `.env`. Key knobs: `MODEL_ID`, `DEVICE` (cpu|cuda),
`DTYPE` (forced to float32 on cpu), `MAX_NEW_TOKENS`, `PORT`, `API_KEY`.

## Layout

- `main.py` -- FastAPI app; model load on lifespan startup, `_infer`/`run_inference`
- `config.py` -- env-driven configuration
- `test_e2e.py` -- end-to-end test

## API

- `GET /health` -- no auth
- `POST /ocr` -- requires `Authorization: Bearer <API_KEY>`

## Deploy

Server-side service: it auto-deploys on git push to `main`. CI (`.gitlab-ci.yml`) builds the
Dockerfile with `docker buildx --push` to the local registry, then bumps the image tag in
the `infrastructure/deploy` repo, which Flux reconciles onto the cluster.

- NEVER restart the running service yourself -- if a restart is needed, tell the user.
- NEVER build/push Docker images by hand; commit + push and let CI handle it.
- NEVER modify Kubernetes env/secrets/deployments directly; changes go through the deploy
  manifests repo so Flux reconciles them.

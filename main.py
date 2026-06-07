import base64
import io
import logging
from contextlib import asynccontextmanager

import torch
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from PIL import Image
from pydantic import BaseModel

from config import MODEL_ID, DEVICE, DTYPE, MAX_NEW_TOKENS, PORT, API_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("ocr")

model = None
processor = None
device = None


def load_model(target_device):
    from transformers import LightOnOcrForConditionalGeneration, LightOnOcrProcessor

    dtype_map = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    torch_dtype = dtype_map.get(DTYPE, torch.bfloat16)
    if target_device == "cpu":
        torch_dtype = torch.float32

    log.info("Loading OCR model '%s' on %s (%s)...", MODEL_ID, target_device, torch_dtype)
    proc = LightOnOcrProcessor.from_pretrained(MODEL_ID)
    mdl = LightOnOcrForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch_dtype,
    ).to(target_device)
    mdl.eval()
    log.info("OCR model loaded on %s.", target_device)
    return mdl, proc


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, processor, device

    device = DEVICE
    model, processor = load_model(device)

    yield
    log.info("Shutting down.")


app = FastAPI(lifespan=lifespan)


def verify_auth(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ")
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _infer(image):
    conversation = [{"role": "user", "content": [{"type": "image", "image": image}]}]
    inputs = processor.apply_chat_template(
        conversation,
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    )
    inputs = {
        k: v.to(device=device, dtype=model.dtype) if v.is_floating_point() else v.to(device)
        for k, v in inputs.items()
    }
    with torch.no_grad():
        output_ids = model.generate(**inputs, max_new_tokens=MAX_NEW_TOKENS)
    generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
    return processor.decode(generated_ids, skip_special_tokens=True)


def run_inference(image):
    try:
        return _infer(image)
    except Exception as e:
        log.error("OCR inference failed: %s", e)
        return None


class OcrRequest(BaseModel):
    image_base64: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/ocr")
async def ocr(
    body: OcrRequest,
    authorization: str | None = Header(None),
):
    verify_auth(authorization)

    try:
        image_data = base64.b64decode(body.image_base64)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
    except Exception as e:
        log.error("Failed to decode image: %s", e)
        raise HTTPException(status_code=400, detail=f"Failed to decode image: {e}")

    width, height = image.size
    log.info("Processing image: %dx%d", width, height)

    text = run_inference(image)
    if text is None:
        raise HTTPException(status_code=500, detail="OCR inference failed")

    log.info("OCR complete: %d characters extracted", len(text))

    return {"text": text, "width": width, "height": height}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)

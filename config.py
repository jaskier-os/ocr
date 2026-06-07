import os
import logging

from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

MODEL_ID = os.environ.get("MODEL_ID", "lightonai/LightOnOCR-2-1B")
DEVICE = os.environ.get("DEVICE", "cpu")
DTYPE = os.environ.get("DTYPE", "float32")
MAX_NEW_TOKENS = int(os.environ.get("MAX_NEW_TOKENS", "4096"))
PORT = int(os.environ.get("PORT", "10006"))

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is required")

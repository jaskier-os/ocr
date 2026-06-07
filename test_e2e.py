"""
E2E test for the OCR microservice.
Requires the service to be running on the configured port.

Usage:
    python test_e2e.py
    python test_e2e.py --image /path/to/image.png
    python test_e2e.py --url http://localhost:10006
"""

import argparse
import base64
import sys
import time
from pathlib import Path

import requests

from config import API_KEY, PORT

DEFAULT_IMAGE = Path.home() / "Downloads" / "kassovyy_onlayn_chek_magazin_lenta_kassopttorg.png"

# Words expected on a Lenta store receipt
EXPECTED_WORDS = ["лента", "итого", "оплат", "сбербанк"]


def test_health(base_url):
    print(f"[test] GET {base_url}/health")
    r = requests.get(f"{base_url}/health", timeout=10)
    assert r.status_code == 200, f"Health check failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["status"] == "ok", f"Unexpected health response: {data}"
    print("[test] Health check passed")


def test_ocr_no_auth(base_url, image_b64):
    print(f"[test] POST {base_url}/ocr without auth")
    r = requests.post(
        f"{base_url}/ocr",
        json={"image_base64": image_b64},
        timeout=600,
    )
    assert r.status_code == 401, f"Expected 401 without auth, got {r.status_code}"
    print("[test] Auth rejection passed")


def test_ocr_bad_key(base_url, image_b64):
    print(f"[test] POST {base_url}/ocr with bad key")
    r = requests.post(
        f"{base_url}/ocr",
        json={"image_base64": image_b64},
        headers={"Authorization": "Bearer wrong-key"},
        timeout=600,
    )
    assert r.status_code == 401, f"Expected 401 with bad key, got {r.status_code}"
    print("[test] Bad key rejection passed")


def test_ocr_bad_image(base_url):
    print(f"[test] POST {base_url}/ocr with invalid base64")
    r = requests.post(
        f"{base_url}/ocr",
        json={"image_base64": "not-valid-base64!!!"},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=600,
    )
    assert r.status_code == 400, f"Expected 400 for bad image, got {r.status_code}"
    print("[test] Bad image rejection passed")


def test_ocr_success(base_url, image_b64):
    print(f"[test] POST {base_url}/ocr with valid receipt image")
    start = time.time()
    r = requests.post(
        f"{base_url}/ocr",
        json={"image_base64": image_b64},
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=600,
    )
    elapsed = time.time() - start
    assert r.status_code == 200, f"OCR failed: {r.status_code} {r.text}"

    data = r.json()
    assert "text" in data, f"Response missing 'text' field: {data}"
    assert "width" in data, f"Response missing 'width' field: {data}"
    assert "height" in data, f"Response missing 'height' field: {data}"
    assert isinstance(data["width"], int) and data["width"] > 0
    assert isinstance(data["height"], int) and data["height"] > 0

    text = data["text"]
    print(f"[test] OCR returned {len(text)} chars in {elapsed:.1f}s")
    print(f"[test] Image dimensions: {data['width']}x{data['height']}")
    print(f"[test] Extracted text (first 500 chars):\n{text[:500]}")

    text_lower = text.lower()
    missing = [w for w in EXPECTED_WORDS if w not in text_lower]
    assert not missing, f"Expected words not found in OCR output: {missing}\nFull text:\n{text}"
    print(f"[test] All expected words found: {EXPECTED_WORDS}")
    print("[test] OCR success test passed")


def main():
    parser = argparse.ArgumentParser(description="E2E test for OCR microservice")
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE, help="Path to test image")
    parser.add_argument("--url", type=str, default=f"http://localhost:{PORT}", help="Service base URL")
    args = parser.parse_args()

    if not args.image.exists():
        print(f"[test] Image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    image_b64 = base64.b64encode(args.image.read_bytes()).decode()
    print(f"[test] Loaded image: {args.image} ({len(image_b64)} base64 chars)")

    base_url = args.url.rstrip("/")
    passed = 0
    failed = 0
    tests = [
        ("health", lambda: test_health(base_url)),
        ("auth_rejection", lambda: test_ocr_no_auth(base_url, image_b64)),
        ("bad_key_rejection", lambda: test_ocr_bad_key(base_url, image_b64)),
        ("bad_image_rejection", lambda: test_ocr_bad_image(base_url)),
        ("ocr_success", lambda: test_ocr_success(base_url, image_b64)),
    ]

    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"[test] FAILED: {name} - {e}", file=sys.stderr)
            failed += 1

    print(f"\n[test] Results: {passed} passed, {failed} failed out of {len(tests)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

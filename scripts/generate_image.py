#!/usr/bin/env python3
"""Generate one manga page through an OpenAI-compatible image API.

Environment:
    IMAGE_API_KEY    API key
    IMAGE_API_BASE   OpenAI-compatible API base, default: https://api.openai.com/v1

Example:
    python scripts/generate_image.py \
      --prompt-file page.txt \
      --out page.png \
      --model gpt-image-2.0 \
      --size 1024x1536 \
      --quality high \
      --ref characters.png \
      --ref location.png
"""

from __future__ import annotations

import argparse
import base64
import io
import os
import sys
import time
import uuid
from pathlib import Path

import requests
from PIL import Image


def compact_image(path: Path, max_side: int = 1152) -> tuple[bytes, str]:
    im = Image.open(path)
    im = im.convert("RGB")
    im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=92, optimize=True)
    return buf.getvalue(), "image/jpeg"


def request_with_retries(method: str, url: str, *, headers: dict, timeout: int = 600, **kwargs) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            resp = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == 3:
                break
            wait = (2**attempt) * 5
            print(f"request retry {attempt + 1}/3 in {wait}s: {exc}", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"image request failed: {last_error}")


def extract_image(payload: dict) -> tuple[str | None, str | None]:
    data = payload.get("data") or []
    if not data:
        return None, None
    item = data[0]
    if item.get("b64_json"):
        return item["b64_json"], None
    if item.get("url"):
        return None, item["url"]
    return None, None


def download(url: str, dst: Path, headers: dict) -> None:
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            with requests.get(url, headers=headers, timeout=300, stream=True) as resp:
                resp.raise_for_status()
                dst.write_bytes(resp.content)
                return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait = (2**attempt) * 3
            print(f"download retry {attempt + 1}/4 in {wait}s: {exc}", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"download failed: {url}: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", help="Prompt text; use --prompt-file for long prompts")
    parser.add_argument("--prompt-file", help="UTF-8 text file containing the prompt")
    parser.add_argument("--out", required=True, help="Output PNG path")
    parser.add_argument("--model", default=os.getenv("IMAGE_MODEL", "gpt-image-2.0"))
    parser.add_argument("--size", default="1024x1536")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high"])
    parser.add_argument("--api-base", default=os.getenv("IMAGE_API_BASE", "https://api.openai.com/v1"))
    parser.add_argument("--ref", action="append", default=[], help="Reference image; repeatable, no hard cap")
    args = parser.parse_args()

    api_key = os.getenv("IMAGE_API_KEY")
    if not api_key:
        raise SystemExit("IMAGE_API_KEY is not set")
    if not args.prompt and not args.prompt_file:
        raise SystemExit("Pass --prompt or --prompt-file")

    prompt = args.prompt or Path(args.prompt_file).read_text(encoding="utf-8")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    api_base = args.api_base.rstrip("/")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": "novel-to-manga-" + uuid.uuid4().hex,
    }

    refs = [Path(p) for p in args.ref]
    if len(refs) > 6:
        print(f"note: {len(refs)} reference images passed; identity fidelity may dilute beyond ~6", file=sys.stderr)
    for ref in refs:
        if not ref.is_file():
            raise SystemExit(f"Reference image not found: {ref}")

    if refs:
        endpoint = f"{api_base}/images/edits"
        files = []
        try:
            for i, ref in enumerate(refs, 1):
                content, mime = compact_image(ref)
                files.append(("image[]", (f"reference-{i}.jpg", content, mime)))
            data = {
                "model": args.model,
                "prompt": prompt,
                "size": args.size,
                "quality": args.quality,
                "n": "1",
            }
            print(f"POST {endpoint} model={args.model} refs={len(refs)}", flush=True)
            resp = request_with_retries("POST", endpoint, headers=headers, data=data, files=files)
        finally:
            del files
    else:
        endpoint = f"{api_base}/images/generations"
        payload = {
            "model": args.model,
            "prompt": prompt,
            "size": args.size,
            "quality": args.quality,
            "n": 1,
        }
        headers["Content-Type"] = "application/json"
        print(f"POST {endpoint} model={args.model}", flush=True)
        resp = request_with_retries("POST", endpoint, headers=headers, json=payload)

    b64, url = extract_image(resp.json())
    if b64:
        out.write_bytes(base64.b64decode(b64))
    elif url:
        download(url, out, {"Authorization": f"Bearer {api_key}"})
    else:
        raise SystemExit(f"No image in response: {str(resp.text)[:500]}")

    print(f"OK {out} ({out.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

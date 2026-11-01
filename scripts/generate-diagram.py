"""Generate a new diagram directly from the checked-in prompt using Gemini."""

import argparse
import base64
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gemini-3-pro-image-preview")
    parser.add_argument(
        "--prompt", type=Path, default=ROOT / "figures/classical-model-prompt.txt"
    )
    parser.add_argument("--reference", type=Path)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "figures/classical-model-generated"
    )
    args = parser.parse_args()
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        parser.error("Set GEMINI_API_KEY in your local environment.")
    parts = []
    if args.reference:
        raw = args.reference.read_bytes()
        if raw.startswith(b"\x89PNG"):
            mime = "image/png"
        elif raw.startswith(b"\xff\xd8"):
            mime = "image/jpeg"
        else:
            parser.error("The reference must be PNG or JPEG.")
        parts.append(
            {"inline_data": {"mime_type": mime, "data": base64.b64encode(raw).decode()}}
        )
    parts.append({"text": args.prompt.read_text()})
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "4:5", "imageSize": "2K"},
        },
    }
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{args.model}:generateContent",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            result = json.load(response)
    except HTTPError as error:
        raise SystemExit(f"Gemini request failed with HTTP {error.code}.") from None
    for candidate in result.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            image = part.get("inlineData")
            if image is None:
                continue
            mime = image.get("mimeType")
            suffix = {"image/png": ".png", "image/jpeg": ".jpg"}.get(mime)
            if suffix is None:
                raise SystemExit(f"Unsupported image format: {mime}")
            output = args.output.with_suffix(suffix)
            if output.exists():
                raise SystemExit(f"Output already exists: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(base64.b64decode(image["data"]))
            print(output)
            return
    raise SystemExit("The response did not contain an image.")


if __name__ == "__main__":
    main()

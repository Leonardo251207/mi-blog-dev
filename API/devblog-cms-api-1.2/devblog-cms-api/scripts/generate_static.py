"""Genera un artefacto HTML estático por cada publicación del CMS.

Uso:
    cd API/devblog-cms-api-1.2/devblog-cms-api
    .venv\\Scripts\\activate
    python scripts/generate_static.py

Requiere que el CMS esté en 8080 y el generador en 8001. Se puede cambiar con
CMS_BASE_URL, CMS_PUBLIC_TOKEN, GENERATOR_BASE_URL y OUTPUT_DIR.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import httpx

CMS_BASE_URL = os.getenv("CMS_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
CMS_TOKEN = os.getenv("CMS_PUBLIC_TOKEN", "public-dev-token")
GENERATOR_BASE_URL = os.getenv("GENERATOR_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
DEFAULT_OUTPUT = Path(__file__).resolve().parents[4] / "dev-blog" / "generated"
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(DEFAULT_OUTPUT)))


def markdown_to_blocks(markdown: str) -> list[dict]:
    """Traduce el Markdown del CMS a los bloques que entiende el generador."""
    lines = str(markdown or "").replace("\r\n", "\n").split("\n")
    blocks: list[dict] = []
    paragraph: list[str] = []
    order = 0

    def push(block_type: str, content_payload: dict) -> None:
        nonlocal order
        order += 1
        blocks.append({
            "block_id": f"blk-{order}",
            "block_type": block_type,
            "order_index": order,
            "content_payload": content_payload,
        })

    def flush() -> None:
        nonlocal paragraph
        if paragraph:
            push("PARAGRAPH", {"text": "\n".join(paragraph)})
            paragraph = []

    index = 0
    while index < len(lines):
        line = lines[index]

        fence = re.match(r"^```(\w+)?\s*$", line)
        if fence:
            flush()
            language = fence.group(1) or ""
            code: list[str] = []
            index += 1
            while index < len(lines) and not re.match(r"^```\s*$", lines[index]):
                code.append(lines[index])
                index += 1
            push("CODE", {"language": language, "code": "\n".join(code)})
            index += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            flush()
            push("HEADING", {"level": len(heading.group(1)), "text": heading.group(2).strip()})
            index += 1
            continue

        if re.match(r"^>\s?", line):
            flush()
            push("QUOTE", {"text": re.sub(r"^>\s?", "", line), "author": ""})
            index += 1
            continue

        image = re.match(r"^\s*!\[([^\]]*)\]\(([^)\s]+)\)\s*$", line)
        if image:
            flush()
            push("IMAGE", {"caption": image.group(1), "url": image.group(2)})
            index += 1
            continue

        if not line.strip():
            flush()
            index += 1
            continue

        paragraph.append(line.strip())
        index += 1

    flush()
    if not blocks:
        push("PARAGRAPH", {"text": "Sin contenido."})
    return blocks


def main() -> None:
    headers = {"Authorization": f"Bearer {CMS_TOKEN}"}
    with httpx.Client(timeout=30.0) as client:
        listing = client.get(f"{CMS_BASE_URL}/api/v1/posts", params={"limit": 50}, headers=headers)
        listing.raise_for_status()
        items = listing.json().get("items", [])
        if not items:
            print("No hay publicaciones para generar.")
            return

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Generando {len(items)} página(s) en {OUTPUT_DIR}")

        for item in items:
            slug = item["slug"]
            detail = client.get(f"{CMS_BASE_URL}/api/v1/posts/slug/{slug}", headers=headers)
            detail.raise_for_status()
            post = detail.json()

            payload = {
                "page_id": f"devblog-{slug}",
                "document_id": post["post_id"],
                "slug": slug,
                "content_type": "DEV_BLOG",
                "engine_hint": "astro",
                "frozen_template": {"engine": "astro"},
                "metadata_values": {
                    "title": post["title"],
                    "tags": post.get("tags", []),
                    "published_at": post.get("published_at"),
                    "reading_time_min": post.get("reading_time_min"),
                    "source": "DevBlog CMS",
                },
                "canvas_blocks": markdown_to_blocks(post.get("content", "")),
                "async_mode": False,
            }

            generated = client.post(f"{GENERATOR_BASE_URL}/api/v1/pages", json=payload)
            generated.raise_for_status()
            result = generated.json()

            artifact = client.get(f"{GENERATOR_BASE_URL}{result['output_url']}")
            artifact.raise_for_status()
            target = OUTPUT_DIR / f"{slug}.html"
            target.write_text(artifact.text, encoding="utf-8")

            print(
                f"+ {slug}: {result.get('status')} · "
                f"{result.get('engine')} · "
                f"{str(result.get('checksum_sha256', ''))[:12]}… -> {target}"
            )


if __name__ == "__main__":
    main()

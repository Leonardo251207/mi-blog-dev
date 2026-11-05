import json
from typing import Dict, Any, List
from src.core.entities import CanvasBlock

class AstroSourceTransformer:
    def transform(self, page_id: str, slug: str, content_type: str, blocks: List[CanvasBlock], metadata: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, str]:
        # Generate frontmatter
        frontmatter = [
            "---",
            f"page_id: \"{page_id}\"",
            f"slug: \"{slug}\"",
            f"content_type: \"{content_type}\"",
            f"layout: \"../../layouts/BaseLayout.astro\"",
        ]
        for k, v in metadata.items():
            frontmatter.append(f"{k}: {json.dumps(v)}")
        frontmatter.append("---\n")

        # Generate markdown / Astro body from canvas blocks
        body = []
        for b in sorted(blocks, key=lambda x: x.order_index):
            b_type = b.block_type.upper()
            payload = b.content_payload
            if b_type == "HEADING":
                level = payload.get("level", 1)
                text = payload.get("text", "")
                body.append(f"{'#' * level} {text}\n")
            elif b_type == "PARAGRAPH":
                body.append(f"{payload.get('text', '')}\n")
            elif b_type == "CODE":
                lang = payload.get("language", "")
                code = payload.get("code", "")
                body.append(f"```{lang}\n{code}\n```\n")
            elif b_type == "IMAGE":
                url = payload.get("url", "")
                caption = payload.get("caption", "image")
                body.append(f"![{caption}]({url})\n")
            elif b_type == "QUOTE":
                text = payload.get("text", "")
                author = payload.get("author", "")
                body.append(f"> {text}\n> — *{author}*\n")
            elif b_type == "SECTION":
                title = payload.get("title", "")
                body.append(f"\n---\n### {title}\n")

        content = "\n".join(frontmatter) + "\n".join(body)

        return {
            "src/pages/index.md": content,
            "astro.config.mjs": "export default { output: 'static' };\n",
            "metadata.json": json.dumps({"page_id": page_id, "slug": slug, "metadata": metadata}, indent=2)
        }

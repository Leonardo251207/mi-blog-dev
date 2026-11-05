import json
from typing import Dict, Any, List
from src.core.entities import CanvasBlock

class QuartoSourceTransformer:
    def transform(self, page_id: str, slug: str, content_type: str, blocks: List[CanvasBlock], metadata: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, str]:
        frontmatter = [
            "---",
            f"title: \"{slug}\"",
            "format:",
            "  html:",
            "    theme: cosmo",
            f"page-id: \"{page_id}\"",
        ]
        for k, v in metadata.items():
            frontmatter.append(f"{k}: {json.dumps(v)}")
        frontmatter.append("---\n")

        body = []
        for b in sorted(blocks, key=lambda x: x.order_index):
            b_type = b.block_type.upper()
            payload = b.content_payload
            if b_type == "HEADING":
                level = payload.get("level", 1)
                body.append(f"{'#' * level} {payload.get('text', '')}\n")
            elif b_type == "PARAGRAPH":
                body.append(f"{payload.get('text', '')}\n")
            elif b_type == "CODE":
                body.append(f"```{payload.get('language', 'python')}\n{payload.get('code', '')}\n```\n")
            elif b_type == "IMAGE":
                body.append(f"![{payload.get('caption', '')}]({payload.get('url', '')})\n")
            elif b_type == "QUOTE":
                body.append(f"> {payload.get('text', '')}\n")

        content = "\n".join(frontmatter) + "\n".join(body)

        return {
            "index.qmd": content,
            "_quarto.yml": f"project:\n  type: website\n  output-dir: _site\n"
        }

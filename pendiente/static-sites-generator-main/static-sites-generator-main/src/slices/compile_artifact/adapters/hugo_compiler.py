from pathlib import Path
from src.core.entities import SourceBundle

class HugoCompilerAdapter:
    def compile(self, bundle: SourceBundle) -> bytes:
        source_content = ""
        for f in bundle.files:
            if f.endswith("_index.md") or f.endswith("index.html"):
                try:
                    with open(f, "r", encoding="utf-8") as sf:
                        source_content = sf.read()
                except Exception:
                    pass
                break

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Hugo Site - {bundle.page_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
        .engine-tag {{ color: #d97706; font-weight: bold; }}
    </style>
</head>
<body>
    <p class="engine-tag">Engine: Hugo Fast Compiler</p>
    <h1>{bundle.page_id}</h1>
    <div>
        <pre>{source_content}</pre>
    </div>
</body>
</html>
"""
        return html.encode("utf-8")

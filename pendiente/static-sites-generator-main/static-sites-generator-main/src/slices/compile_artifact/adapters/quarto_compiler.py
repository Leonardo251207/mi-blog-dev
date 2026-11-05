from pathlib import Path
from src.core.entities import SourceBundle

class QuartoCompilerAdapter:
    def compile(self, bundle: SourceBundle) -> bytes:
        source_content = ""
        for f in bundle.files:
            if f.endswith("index.qmd"):
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
    <title>Quarto Doc - {bundle.page_id}</title>
    <style>
        body {{ font-family: 'Georgia', serif; line-height: 1.8; max-width: 820px; margin: 40px auto; padding: 0 20px; color: #1a202c; }}
        .header {{ border-bottom: 1px solid #cbd5e1; margin-bottom: 2rem; }}
        .badge {{ background-color: #4338ca; color: white; padding: 2px 6px; border-radius: 4px; font-family: sans-serif; font-size: 0.8rem; }}
    </style>
</head>
<body>
    <div class="header">
        <span class="badge">Quarto Scientific/Technical</span>
        <h2>{bundle.page_id}</h2>
    </div>
    <div>
        <pre>{source_content}</pre>
    </div>
</body>
</html>
"""
        return html.encode("utf-8")

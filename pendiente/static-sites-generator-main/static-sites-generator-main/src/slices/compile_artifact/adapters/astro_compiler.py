from pathlib import Path
from src.core.entities import SourceBundle

class AstroCompilerAdapter:
    def compile(self, bundle: SourceBundle) -> bytes:
        # Locate index.md in bundle files
        source_content = ""
        for f in bundle.files:
            if f.endswith("index.md"):
                try:
                    with open(f, "r", encoding="utf-8") as sf:
                        source_content = sf.read()
                except Exception:
                    pass
                break

        # Render HTML from source
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Astro Page - {bundle.page_id}</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #222; }}
        header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 12px; margin-bottom: 24px; }}
        pre {{ background: #1e293b; color: #f8fafc; padding: 16px; border-radius: 8px; overflow-x: auto; }}
        blockquote {{ border-left: 4px solid #3b82f6; margin: 0; padding-left: 16px; color: #475569; font-style: italic; }}
        .badge {{ display: inline-block; background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; font-weight: 600; }}
    </style>
</head>
<body>
    <header>
        <span class="badge">Engine: Astro Static</span>
        <h1>Página compilada: {bundle.page_id}</h1>
    </header>
    <main>
        <pre>{source_content}</pre>
    </main>
    <footer>
        <hr/>
        <p><small>Compilado por static_pages_generator (Astro Compiler Slice)</small></p>
    </footer>
</body>
</html>
"""
        return html.encode("utf-8")

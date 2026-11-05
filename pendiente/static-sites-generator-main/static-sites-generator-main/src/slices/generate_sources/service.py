from typing import Dict, Any, List
from src.core.entities import SourceBundle, EngineType, CanvasBlock
from src.core.errors import UnsupportedEngineError
from .ports import GenerateSourcesPort, SourceTransformerPort, SourceStoragePort
from .adapters import AstroSourceTransformer, HugoSourceTransformer, QuartoSourceTransformer

class GenerateSourcesService(GenerateSourcesPort):
    def __init__(self, storage_port: SourceStoragePort):
        self.storage = storage_port
        self.transformers: Dict[EngineType, SourceTransformerPort] = {
            EngineType.ASTRO: AstroSourceTransformer(),
            EngineType.HUGO: HugoSourceTransformer(),
            EngineType.QUARTO: QuartoSourceTransformer(),
        }

    def _resolve_engine(self, snapshot: Dict[str, Any]) -> EngineType:
        # Check engine_hint
        engine_hint = snapshot.get("engine_hint")
        if engine_hint:
            try:
                return EngineType(engine_hint.lower())
            except ValueError:
                pass
        
        # Check frozen_template
        frozen_template = snapshot.get("frozen_template") or {}
        if isinstance(frozen_template, dict):
            eng = frozen_template.get("engine")
            if eng:
                try:
                    return EngineType(eng.lower())
                except ValueError:
                    pass

        # Check content_type defaults
        content_type = snapshot.get("content_type", "")
        if "DEV_DOC" in content_type:
            return EngineType.QUARTO
        elif "BLOG" in content_type:
            return EngineType.HUGO

        return EngineType.ASTRO

    def execute(self, snapshot: Dict[str, Any]) -> SourceBundle:
        page_id = snapshot["page_id"]
        slug = snapshot.get("slug", page_id)
        content_type = snapshot.get("content_type", "GENERIC")
        metadata = snapshot.get("metadata_values", {})
        frozen_template = snapshot.get("frozen_template", {})

        raw_blocks = snapshot.get("canvas_blocks", [])
        blocks = [
            CanvasBlock(
                block_id=b.get("block_id", f"b-{i}"),
                block_type=b.get("block_type", "PARAGRAPH"),
                order_index=b.get("order_index", i),
                content_payload=b.get("content_payload", {}),
                style_config=b.get("style_config")
            )
            for i, b in enumerate(raw_blocks)
        ]

        engine = self._resolve_engine(snapshot)
        transformer = self.transformers.get(engine)
        if not transformer:
            raise UnsupportedEngineError(engine.value)

        # Generate files dictionary
        files_dict = transformer.transform(
            page_id=page_id,
            slug=slug,
            content_type=content_type,
            blocks=blocks,
            metadata=metadata,
            template=frozen_template
        )

        # Save files to source storage
        saved_paths: List[str] = []
        for rel_path, content in files_dict.items():
            full_path = self.storage.save_source_file(page_id, rel_path, content)
            saved_paths.append(full_path)

        return SourceBundle(
            page_id=page_id,
            engine=engine,
            sources_path=page_id,
            files=saved_paths
        )

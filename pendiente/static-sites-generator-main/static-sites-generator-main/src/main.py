from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import SQLITE_DB_PATH
from src.shared.database import init_db
from src.adapters.driven.sqlite_page_repository import SqlitePageRepository
from src.adapters.driven.sqlite_artifact_repository import SqliteArtifactRepository
from src.adapters.driven.local_storage_adapter import LocalStorageAdapter
from src.slices.generate_sources.service import GenerateSourcesService
from src.slices.compile_artifact.service import CompileArtifactService
from src.slices.manage_artifacts.service import ManageArtifactsService
from src.adapters.driving.router import router, set_dependencies

# Ensure database schema is initialized on load
init_db(SQLITE_DB_PATH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema on server startup
    init_db(SQLITE_DB_PATH)
    yield

app = FastAPI(
    title="static_pages_generator",
    description="Hexagonal & Vertical Slice Static Page Generator Pipeline",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Composition Root - Wire Dependencies
page_repo = SqlitePageRepository()
artifact_repo = SqliteArtifactRepository()
storage = LocalStorageAdapter()

generate_service = GenerateSourcesService(storage_port=storage)
compile_service = CompileArtifactService(
    storage_port=storage,
    artifact_repo=artifact_repo,
    build_repo=page_repo
)
manage_service = ManageArtifactsService(
    artifact_repo=artifact_repo,
    page_repo=page_repo,
    storage=storage,
    generate_service=generate_service,
    compile_service=compile_service
)

set_dependencies(
    page_repo=page_repo,
    artifact_repo=artifact_repo,
    generate_service=generate_service,
    compile_service=compile_service,
    manage_service=manage_service
)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "static_pages_generator"}

if __name__ == "__main__":
    import uvicorn
    from src.config import HOST, PORT
    uvicorn.run("src.main:app", host=HOST, port=PORT, reload=True)

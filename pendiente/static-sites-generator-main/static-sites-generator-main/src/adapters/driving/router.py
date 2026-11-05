import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Response, Depends, status
from fastapi.responses import HTMLResponse

from src.core.entities import Page, PageStatus, BuildStatus
from src.core.errors import PageNotFoundError, ArtifactNotFoundError, DomainException
from src.adapters.driving.schemas import (
    PageCreationPayload,
    PageResponse,
    BuildResponse,
    IntegrityResponse
)
from src.adapters.driven.sqlite_page_repository import SqlitePageRepository
from src.adapters.driven.sqlite_artifact_repository import SqliteArtifactRepository
from src.slices.generate_sources.ports import GenerateSourcesPort
from src.slices.compile_artifact.ports import CompileArtifactPort
from src.slices.manage_artifacts.ports import ManageArtifactsPort

router = APIRouter(prefix="/api/v1")

# Dependencies injection container references (initialized in main.py)
_page_repo: Optional[SqlitePageRepository] = None
_artifact_repo: Optional[SqliteArtifactRepository] = None
_generate_service: Optional[GenerateSourcesPort] = None
_compile_service: Optional[CompileArtifactPort] = None
_manage_service: Optional[ManageArtifactsPort] = None

def set_dependencies(
    page_repo: SqlitePageRepository,
    artifact_repo: SqliteArtifactRepository,
    generate_service: GenerateSourcesPort,
    compile_service: CompileArtifactPort,
    manage_service: ManageArtifactsPort
):
    global _page_repo, _artifact_repo, _generate_service, _compile_service, _manage_service
    _page_repo = page_repo
    _artifact_repo = artifact_repo
    _generate_service = generate_service
    _compile_service = compile_service
    _manage_service = manage_service

def _run_pipeline(page_id: str, snapshot: dict, build_id: str):
    # Slice 1: Generate sources
    bundle = _generate_service.execute(snapshot)
    # Slice 2: Compile artifact
    artifact, build_job = _compile_service.execute(bundle, build_id)
    # Update page record
    page = _page_repo.get_page(page_id)
    if page:
        page.build_id = build_id
        page.output_url = f"/api/v1/pages/{page_id}/content"
        page.status = PageStatus.COMPLETED
        _page_repo.save_page(page)

@router.post("/pages", response_model=PageResponse)
def create_page(payload: PageCreationPayload, background_tasks: BackgroundTasks, response: Response):
    # If slug already exists, reuse its page_id for recompilation / re-dispatch
    existing_page = _page_repo.get_by_slug(payload.slug)
    if existing_page:
        page_id = existing_page.page_id
    else:
        page_id = payload.page_id or f"page-{uuid.uuid4().hex[:12]}"

    build_id = f"bld-{uuid.uuid4().hex[:12]}"
    snapshot_dict = payload.model_dump()
    snapshot_dict["page_id"] = page_id

    # 1. Store/update page in repository
    page = Page(
        page_id=page_id,
        document_id=payload.document_id,
        slug=payload.slug,
        content_type=payload.content_type,
        status=PageStatus.GENERATING,
        build_id=build_id,
        output_url=f"/api/v1/pages/{page_id}/content",
        source_snapshot=snapshot_dict
    )
    _page_repo.save_page(page)

    if payload.async_mode:
        # Asynchronous processing (SLA > 10s rule -> 202 Accepted)
        background_tasks.add_task(_run_pipeline, page_id, snapshot_dict, build_id)
        response.status_code = status.HTTP_202_ACCEPTED
        return PageResponse(
            page_id=page_id,
            document_id=page.document_id,
            slug=page.slug,
            content_type=page.content_type,
            status=PageStatus.GENERATING.value,
            build_id=build_id,
            output_url=page.output_url,
            created_at=page.created_at
        )

    # Synchronous processing (SLA < 10s rule -> 201 Created)
    try:
        # 2. Slice 1: Generate sources
        bundle = _generate_service.execute(snapshot_dict)
        # 3. Slice 2: Compile artifact + calculate SHA-256
        artifact, build_job = _compile_service.execute(bundle, build_id)

        # 4. Update page to COMPLETED
        page.status = PageStatus.COMPLETED
        _page_repo.save_page(page)

        response.status_code = status.HTTP_201_CREATED
        return PageResponse(
            page_id=page_id,
            document_id=page.document_id,
            slug=page.slug,
            content_type=page.content_type,
            status=page.status.value,
            build_id=build_id,
            output_url=page.output_url,
            checksum_sha256=artifact.checksum_sha256,
            engine=bundle.engine.value,
            created_at=page.created_at
        )
    except DomainException as e:
        page.status = PageStatus.FAILED
        _page_repo.save_page(page)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        page.status = PageStatus.FAILED
        _page_repo.save_page(page)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

@router.get("/pages/{page_id}", response_model=PageResponse)
def get_page(page_id: str):
    page = _page_repo.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found.")
    
    artifact = _artifact_repo.get_by_page_id(page_id)
    checksum = artifact.checksum_sha256 if artifact else None

    return PageResponse(
        page_id=page.page_id,
        document_id=page.document_id,
        slug=page.slug,
        content_type=page.content_type,
        status=page.status.value,
        build_id=page.build_id,
        output_url=page.output_url,
        checksum_sha256=checksum,
        created_at=page.created_at
    )

@router.get("/pages/{page_id}/content", response_class=HTMLResponse)
def get_page_content(page_id: str):
    try:
        content_bytes, mime_type = _manage_service.get_content(page_id)
        return Response(content=content_bytes, media_type=mime_type)
    except PageNotFoundError:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found.")
    except ArtifactNotFoundError:
        raise HTTPException(status_code=404, detail=f"Artifact for page '{page_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve artifact: {str(e)}")

@router.get("/pages/{page_id}/verify", response_model=IntegrityResponse)
def verify_page_integrity(page_id: str, auto_repair: bool = True):
    try:
        result = _manage_service.verify_integrity(page_id, auto_repair=auto_repair)
        return IntegrityResponse(**result)
    except PageNotFoundError:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found.")
    except ArtifactNotFoundError:
        raise HTTPException(status_code=404, detail=f"Artifact for page '{page_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integrity check failed: {str(e)}")

@router.post("/pages/{page_id}/rebuild", response_model=PageResponse)
def rebuild_page(page_id: str):
    try:
        artifact = _manage_service.rebuild(page_id)
        page = _page_repo.get_page(page_id)
        return PageResponse(
            page_id=page.page_id,
            document_id=page.document_id,
            slug=page.slug,
            content_type=page.content_type,
            status=page.status.value,
            build_id=page.build_id,
            output_url=page.output_url,
            checksum_sha256=artifact.checksum_sha256,
            created_at=page.created_at
        )
    except PageNotFoundError:
        raise HTTPException(status_code=404, detail=f"Page '{page_id}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")

@router.get("/builds/{build_id}", response_model=BuildResponse)
def get_build(build_id: str):
    build = _page_repo.get_build(build_id)
    if not build:
        raise HTTPException(status_code=404, detail=f"Build '{build_id}' not found.")
    return BuildResponse(
        build_id=build.build_id,
        page_id=build.page_id,
        engine=build.engine.value,
        status=build.status.value,
        error_message=build.error_message,
        started_at=build.started_at,
        completed_at=build.completed_at
    )

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas.file import FileListResponse, FileResponse
from app.services.file import FileService

router = APIRouter(prefix="/files", tags=["files"])


def get_file_service(db: Annotated[Session, Depends(get_db)]) -> FileService:
    return FileService(db)


@router.post("/", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> FileResponse:
    return await file_service.upload(file, current_user)


@router.get("/", response_model=FileListResponse)
def list_files(
    current_user: Annotated[User, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> FileListResponse:
    from app.schemas.file import PaginationParams

    pagination = PaginationParams(page=page, page_size=page_size)
    return file_service.list_files(current_user, pagination)


@router.get("/{file_id}")
def download_file(
    file_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> FastAPIFileResponse:
    record = file_service.get_file_record(file_id, current_user)
    path = file_service.get_file_path(record)
    return FastAPIFileResponse(
        path=path,
        filename=record.original_filename,
        media_type=record.content_type or "application/octet-stream",
    )


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)],
) -> None:
    file_service.delete(file_id, current_user)

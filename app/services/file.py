import os
import uuid
from pathlib import Path

import aiofiles
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import FileRecord, User
from app.schemas.file import FileListResponse, FileResponse, PaginationParams


class FileService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str | None) -> str:
        if not filename:
            return "unnamed"
        return os.path.basename(filename)

    async def upload(self, upload_file: UploadFile, owner: User) -> FileResponse:
        original_filename = self._sanitize_filename(upload_file.filename)
        stored_filename = str(uuid.uuid4())
        stored_path = self.upload_dir / stored_filename

        size_bytes = 0
        try:
            async with aiofiles.open(stored_path, "wb") as out_file:
                while chunk := await upload_file.read(1024 * 1024):
                    size_bytes += len(chunk)
                    if size_bytes > settings.max_file_size_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"File exceeds maximum size of {settings.max_file_size_mb} MB",
                        )
                    await out_file.write(chunk)
        except HTTPException:
            if stored_path.exists():
                stored_path.unlink()
            raise
        except Exception as exc:
            if stored_path.exists():
                stored_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save file",
            ) from exc
        finally:
            await upload_file.close()

        if size_bytes == 0:
            if stored_path.exists():
                stored_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        record = FileRecord(
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=upload_file.content_type,
            size_bytes=size_bytes,
            owner_id=owner.id,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return FileResponse.model_validate(record)

    def list_files(self, owner: User, pagination: PaginationParams) -> FileListResponse:
        query = self.db.query(FileRecord).filter(FileRecord.owner_id == owner.id)
        total = query.with_entities(func.count(FileRecord.id)).scalar() or 0
        records = (
            query.order_by(FileRecord.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
            .all()
        )
        return FileListResponse(
            items=[FileResponse.model_validate(record) for record in records],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pagination.pages_count(total),
        )

    def get_file_record(self, file_id: uuid.UUID, owner: User) -> FileRecord:
        record = (
            self.db.query(FileRecord)
            .filter(FileRecord.id == file_id, FileRecord.owner_id == owner.id)
            .first()
        )
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )
        return record

    def get_file_path(self, record: FileRecord) -> Path:
        path = self.upload_dir / record.stored_filename
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk",
            )
        return path

    def delete(self, file_id: uuid.UUID, owner: User) -> None:
        record = self.get_file_record(file_id, owner)
        path = self.upload_dir / record.stored_filename
        if path.exists():
            path.unlink()
        self.db.delete(record)
        self.db.commit()

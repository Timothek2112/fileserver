from datetime import datetime
from math import ceil
from uuid import UUID

from pydantic import BaseModel, Field


class FileResponse(BaseModel):
    id: UUID
    original_filename: str
    content_type: str | None
    size_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    items: list[FileResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def pages_count(self, total: int) -> int:
        if total == 0:
            return 0
        return ceil(total / self.page_size)

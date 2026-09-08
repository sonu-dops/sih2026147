"""Signal file and metadata repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models.signal import SignalFile, SignalMetadata
from backend.app.db.repositories.base import BaseRepository


class SignalRepository(BaseRepository[SignalFile]):
    def __init__(self, db: Session):
        super().__init__(SignalFile, db)

    def get_by_hash(self, file_hash: str) -> Optional[SignalFile]:
        stmt = select(SignalFile).where(SignalFile.file_hash == file_hash)
        return self.db.scalars(stmt).first()

    def get_with_metadata(self, signal_id: int) -> Optional[SignalFile]:
        stmt = (
            select(SignalFile)
            .where(SignalFile.id == signal_id)
            .options(selectinload(SignalFile.metadata_records))
        )
        return self.db.scalars(stmt).first()

    def list_by_project(self, project_id: Optional[int], skip: int = 0, limit: int = 100) -> List[SignalFile]:
        stmt = select(SignalFile)
        if project_id is not None:
            stmt = stmt.where(SignalFile.project_id == project_id)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def add_metadata(self, metadata: SignalMetadata) -> SignalMetadata:
        self.db.add(metadata)
        self.db.commit()
        self.db.refresh(metadata)
        return metadata

    def add_metadata_batch(self, items: List[SignalMetadata]) -> List[SignalMetadata]:
        self.db.add_all(items)
        self.db.commit()
        return items

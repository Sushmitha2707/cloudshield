from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class StoredFile(Base):
    """One row per filename we protect."""
    __tablename__ = "stored_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    jobs: Mapped[list["BackupJob"]] = relationship(back_populates="file")


class BackupJob(Base):
    """One row per backup attempt = one version of a file."""
    __tablename__ = "backup_jobs"
    __table_args__ = (UniqueConstraint("file_id", "version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("stored_files.id"))
    version: Mapped[int]
    size_bytes: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="queued")
    error: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    file: Mapped["StoredFile"] = relationship(back_populates="jobs")
    
class JobChunk(Base):
    """Which chunks, in order, make up one version of a file."""
    __tablename__ = "job_chunks"

    job_id: Mapped[int] = mapped_column(ForeignKey("backup_jobs.id"), primary_key=True)
    chunk_index: Mapped[int] = mapped_column(primary_key=True)
    checksum: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int]
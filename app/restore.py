from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chunking import sha256_hex
from app.config import CHUNKS_CONTAINER
from app.models import JobChunk
from app.storage import download_blob


class IntegrityError(Exception):
    """Raised when a stored chunk no longer matches its fingerprint."""


def rebuild_file(db: Session, job_id: int) -> bytes:
    """Fetch every chunk of one version in order, verify each, and join them."""
    rows = db.scalars(
        select(JobChunk).where(JobChunk.job_id == job_id).order_by(JobChunk.chunk_index)
    ).all()
    if not rows:
        raise IntegrityError(f"No chunks recorded for job {job_id}")

    parts = []
    for row in rows:
        data = download_blob(CHUNKS_CONTAINER, row.checksum)
        if sha256_hex(data) != row.checksum:
            raise IntegrityError(f"Chunk {row.chunk_index} is corrupted (checksum mismatch)")
        parts.append(data)
    return b"".join(parts)
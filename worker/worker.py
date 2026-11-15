import logging
import os

from app.chunking import split_into_chunks
from app.config import CHUNKS_CONTAINER, STAGING_CONTAINER
from app.database import SessionLocal
from app.job_queue import dequeue_job
from app.models import BackupJob, JobChunk
from app.storage import download_blob, ensure_container, upload_blob

logging.basicConfig(level=logging.INFO, format="%(asctime)s [worker %(process)d] %(message)s")
log = logging.getLogger("worker")
logging.getLogger("azure").setLevel(logging.WARNING)

def process_job(job_id: int) -> None:
    db = SessionLocal()
    try:
        job = db.get(BackupJob, job_id)
        if job is None:
            log.warning("job %s not found, skipping", job_id)
            return

        job.status = "running"
        db.commit()
        log.info("job %s: started (%s bytes)", job_id, job.size_bytes)

        data = download_blob(STAGING_CONTAINER, f"job-{job_id}")
        count = 0
        for index, chunk, checksum in split_into_chunks(data):
            upload_blob(CHUNKS_CONTAINER, checksum, chunk)
            db.add(JobChunk(job_id=job_id, chunk_index=index,
                            checksum=checksum, size_bytes=len(chunk)))
            count += 1

        job.status = "completed"
        db.commit()
        log.info("job %s: completed, %s chunk(s) stored", job_id, count)
    except Exception as exc:
        db.rollback()
        job = db.get(BackupJob, job_id)
        if job is not None:
            job.status = "failed"
            job.error = str(exc)[:500]
            db.commit()
        log.error("job %s: failed: %s", job_id, exc)
    finally:
        db.close()


def main() -> None:
    ensure_container(CHUNKS_CONTAINER)
    log.info("worker ready, waiting for jobs")
    while True:
        job_id = dequeue_job()
        if job_id is None:
            continue
        process_job(job_id)


if __name__ == "__main__":
    main()
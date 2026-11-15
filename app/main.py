from contextlib import asynccontextmanager
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import STAGING_CONTAINER
from app.database import Base, engine, get_db
from app.job_queue import enqueue_job
from app.models import BackupJob, StoredFile
from app.restore import IntegrityError, rebuild_file
from app.storage import ensure_container, upload_blob

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)       # create tables if missing
    ensure_container(STAGING_CONTAINER)    # create the staging container if missing
    yield


app = FastAPI(title="CloudShield", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/backups", status_code=202)
def create_backup(file: UploadFile, db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a name")
    data = file.file.read()
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    stored = db.scalar(select(StoredFile).where(StoredFile.filename == file.filename))
    if stored is None:
        stored = StoredFile(filename=file.filename)
        db.add(stored)
        db.flush()

    last = db.scalar(
        select(func.max(BackupJob.version)).where(BackupJob.file_id == stored.id)
    ) or 0
    job = BackupJob(file_id=stored.id, version=last + 1, size_bytes=len(data), status="queued")
    db.add(job)
    db.flush()

    upload_blob(STAGING_CONTAINER, f"job-{job.id}", data)
    db.commit()
    enqueue_job(job.id)
    return {
        "job_id": job.id,
        "filename": stored.filename,
        "version": job.version,
        "size_bytes": job.size_bytes,
        "status": job.status,
    }


@app.get("/backups/{job_id}")
def get_backup(job_id: int, db: Session = Depends(get_db)):
    job = db.get(BackupJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Backup job not found")
    return {
        "job_id": job.id,
        "filename": job.file.filename,
        "version": job.version,
        "size_bytes": job.size_bytes,
        "status": job.status,
        "error": job.error,
        "created_at": job.created_at,
    }


@app.get("/files")
def list_files(db: Session = Depends(get_db)):
    files = db.scalars(select(StoredFile).order_by(StoredFile.filename)).all()
    return [
        {
            "filename": f.filename,
            "versions": [
                {
                    "version": j.version,
                    "status": j.status,
                    "size_bytes": j.size_bytes,
                    "created_at": j.created_at,
                }
                for j in sorted(f.jobs, key=lambda j: j.version)
            ],
        }
        for f in files
    ]

@app.get("/files/{filename}/versions/{version}/restore")
def restore_version(filename: str, version: int, db: Session = Depends(get_db)):
    job = db.scalar(
        select(BackupJob)
        .join(StoredFile)
        .where(StoredFile.filename == filename, BackupJob.version == version)
    )
    if job is None:
        raise HTTPException(status_code=404, detail="That file version does not exist")
    if job.status != "completed":
        raise HTTPException(status_code=409, detail=f"Backup is not ready (status: {job.status})")

    try:
        data = rebuild_file(db, job.id)
    except IntegrityError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return Response(
        content=data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
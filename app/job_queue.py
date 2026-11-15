import redis

from app.config import REDIS_URL

QUEUE_NAME = "backup_jobs"
_redis = redis.Redis.from_url(REDIS_URL, socket_timeout=30)


def enqueue_job(job_id: int) -> None:
    """Put a job number at the back of the line."""
    _redis.lpush(QUEUE_NAME, job_id)


def dequeue_job(timeout: int = 5):
    """Wait up to `timeout` seconds for a job. Returns the job number, or None if the line stayed empty."""
    item = _redis.brpop(QUEUE_NAME, timeout=timeout)
    if item is None:
        return None
    return int(item[1])
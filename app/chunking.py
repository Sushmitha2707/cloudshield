import hashlib

CHUNK_SIZE = 1024 * 1024  # 1 MiB


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 fingerprint of some bytes as a text string."""
    return hashlib.sha256(data).hexdigest()


def split_into_chunks(data: bytes, chunk_size: int = CHUNK_SIZE):
    """Cut data into pieces. Gives back (index, chunk_bytes, checksum) for each piece."""
    for index, start in enumerate(range(0, len(data), chunk_size)):
        chunk = data[start:start + chunk_size]
        yield index, chunk, sha256_hex(chunk)
from app.chunking import CHUNK_SIZE, sha256_hex, split_into_chunks


def test_same_data_gives_same_checksum():
    assert sha256_hex(b"hello") == sha256_hex(b"hello")


def test_one_byte_change_gives_different_checksum():
    assert sha256_hex(b"hello") != sha256_hex(b"hellp")


def test_split_and_rejoin_gives_original_file():
    data = b"x" * (CHUNK_SIZE * 2 + 500)
    chunks = list(split_into_chunks(data))
    assert len(chunks) == 3
    assert b"".join(chunk for _, chunk, _ in chunks) == data


def test_each_checksum_matches_its_chunk():
    data = bytes(range(256)) * 10
    for _, chunk, checksum in split_into_chunks(data, chunk_size=100):
        assert sha256_hex(chunk) == checksum
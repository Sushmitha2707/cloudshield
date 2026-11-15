from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from app.config import AZURE_CONN_STR

_client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)


def ensure_container(name: str) -> None:
    try:
        _client.create_container(name)
    except ResourceExistsError:
        pass


def upload_blob(container: str, name: str, data: bytes) -> None:
    _client.get_blob_client(container, name).upload_blob(data, overwrite=True)
    
def download_blob(container: str, name: str) -> bytes:
    return _client.get_blob_client(container, name).download_blob().readall()

def blob_exists(container: str, name: str) -> bool:
    return _client.get_blob_client(container, name).exists()
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://cloudshield:cloudshield@localhost:5432/cloudshield",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
AZURE_CONN_STR = os.getenv(
    "AZURE_STORAGE_CONNECTION_STRING",
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;",
)
STAGING_CONTAINER = "staging"
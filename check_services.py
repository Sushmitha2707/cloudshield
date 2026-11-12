import psycopg
import redis
from azure.storage.blob import BlobServiceClient

# Postgres
with psycopg.connect("postgresql://cloudshield:cloudshield@localhost:5432/cloudshield") as conn:
    print("Postgres OK:", conn.execute("select 1").fetchone())

# Redis
r = redis.Redis(host="localhost", port=6379)
print("Redis OK:", r.ping())

# Azurite (the public dev account used by the emulator, not a secret)
conn_str = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)
client = BlobServiceClient.from_connection_string(conn_str)
try:
    client.create_container("test")
except Exception:
    pass
print("Azurite OK:", [c.name for c in client.list_containers()])

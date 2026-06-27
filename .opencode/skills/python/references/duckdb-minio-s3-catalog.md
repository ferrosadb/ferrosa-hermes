# DuckDB + MinIO/S3 Parquet Catalog Verification

Use this reference when a Python project uses DuckDB over partitioned Parquet and needs a local S3-compatible smoke test before real object storage.

## Pattern

1. Keep the application query path identical for local files and S3 URIs.
   - Local: `./data/catalog/**/*.parquet`
   - S3/MinIO: `s3://bucket/prefix/**/*.parquet`
2. Write Parquet through PyArrow with a filesystem abstraction.
   - Local writes use plain `base_dir`.
   - S3 writes use `pyarrow.fs.S3FileSystem` and a `bucket/prefix` base dir, not the raw `s3://...` string.
3. Read through DuckDB with the `httpfs` extension and an S3 secret.
4. Use path-style URLs for MinIO.
5. Verify by writing fixture rows, reading summaries through the same public catalog/API helper, and then hitting the API path.

## Compose fixture

```yaml
services:
  minio:
    image: minio/minio:RELEASE.2025-04-08T15-41-24Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-dev}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-dev-secret}
    ports:
      - "${MINIO_API_PORT:-9100}:9000"
      - "${MINIO_CONSOLE_PORT:-9101}:9001"
    volumes:
      - minio_data:/data

  minio-create-bucket:
    image: minio/mc:RELEASE.2025-04-08T15-39-49Z
    depends_on: [minio]
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-dev}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-dev-secret}
      MINIO_BUCKET: ${MINIO_BUCKET:-catalog}
    entrypoint: ["/bin/sh", "-c"]
    command: |
      until mc alias set local http://minio:9000 "$${MINIO_ROOT_USER}" "$${MINIO_ROOT_PASSWORD}"; do sleep 1; done
      mc mb --ignore-existing "local/$${MINIO_BUCKET}"
      mc ls "local/$${MINIO_BUCKET}"

volumes:
  minio_data:
```

## DuckDB S3 setup

```python
import duckdb

con = duckdb.connect()
con.execute("INSTALL httpfs")
con.execute("LOAD httpfs")
con.execute("""
CREATE OR REPLACE SECRET catalog_s3 (
  TYPE S3,
  KEY_ID 'dev',
  SECRET 'dev-secret',
  REGION 'us-east-1',
  ENDPOINT 'localhost:9100',
  URL_STYLE 'path',
  USE_SSL false
)
""")
rows = con.execute(
    "SELECT event_type, count(*) FROM read_parquet('s3://catalog/prefix/**/*.parquet', hive_partitioning=true) GROUP BY 1"
).fetchall()
```

## PyArrow S3 write target

```python
from urllib.parse import urlparse
from pyarrow import fs as pafs
import pyarrow.dataset as pads

uri = "s3://catalog/prefix"
parsed = urlparse(uri)
filesystem = pafs.S3FileSystem(
    access_key="dev",
    secret_key="dev-secret",
    region="us-east-1",
    scheme="http",
    endpoint_override="localhost:9100",
)
pads.write_dataset(
    table,
    base_dir=f"{parsed.netloc}/{parsed.path.lstrip('/')}",
    filesystem=filesystem,
    format="parquet",
    partitioning=["event_type", "date"],
    partitioning_flavor="hive",
)
```

## Verification checklist

- `ruff check` on changed Python files.
- Full pytest suite or focused catalog/API tests.
- Start MinIO and bucket-init service.
- Seed deterministic fixture data to `s3://...`.
- Read back through the production catalog helper, not ad hoc filesystem listing.
- Hit the API with `CATALOG_PATH=s3://...` to prove the web boundary uses the same DuckDB path.

## Pitfalls

- Do not record `http://` in the DuckDB `ENDPOINT`; DuckDB expects host:port plus `USE_SSL false` for MinIO.
- PyArrow's S3 filesystem expects `endpoint_override` without a scheme and `scheme="http"` for MinIO.
- A local `s3://...` existence check cannot glob like the filesystem. Let DuckDB/PyArrow fail loud if the bucket/path is wrong.
- Keep credentials dev-only in `.env.example`; do not bake real cloud credentials into compose files.

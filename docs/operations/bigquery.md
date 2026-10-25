# BigQuery analytics export

`python -m analytics prepare --database PATH --output artifacts/exports` writes an immutable NDJSON batch and JSON manifest locally. `python -m analytics inspect --manifest PATH` verifies the SHA-256, row count and manifest consistency; neither command imports a Google SDK or reads ADC.

The later `upload` phase is intentionally separate and requires explicit project, dataset, bucket and location configuration. It uploads the immutable batch, executes an idempotent load followed by a version-aware merge, and acknowledges the operational outbox only after both jobs succeed. `record_version` is authoritative; archived/deleted rows remain as tombstones and are excluded from `published_news`.

Before any real upload, validate local output and take a database backup. Never put credentials in this repository or in NDJSON rows. Cloud resources, billing, permissions and upload are not covered by local tests.

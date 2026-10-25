"""Safe local adoption entrypoint. It preserves known legacy news rows and IDs."""
from __future__ import annotations
from pathlib import Path
from sqlalchemy import inspect, text
from database import make_engine, Base
import models  # register mappings; keep one metadata registry in app-dir mode

LEGACY = {"id", "title", "summary", "content", "category", "university", "author", "image_url", "source_url", "is_featured", "created_at", "updated_at"}
def bootstrap_database(url: str) -> None:
    engine = make_engine(url); inspector = inspect(engine)
    if "news" in inspector.get_table_names():
        columns = {item["name"] for item in inspector.get_columns("news")}
        if not LEGACY <= columns: raise RuntimeError("unknown_legacy_schema")
        # Additive migration is deliberately idempotent; SQLite cannot add constraints safely.
        additions = {"published_at":"DATETIME", "university_id":"INTEGER", "source_id":"INTEGER", "canonical_url":"TEXT", "content_hash":"VARCHAR(64)", "published_on":"DATE", "date_precision":"VARCHAR(10)", "publication_status":"VARCHAR(12) DEFAULT 'published'", "editorial_lock":"BOOLEAN DEFAULT 1", "last_fetched_at":"DATETIME", "image_status":"VARCHAR(12) DEFAULT 'not_found'", "image_sha256":"VARCHAR(64)", "image_original_url":"TEXT", "image_alt":"TEXT", "image_credit":"TEXT"}
        with engine.begin() as conn:
            for name, typ in additions.items():
                if name not in columns: conn.execute(text(f"ALTER TABLE news ADD COLUMN {name} {typ}"))
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        # Historical rows are publications protected from automated replacement.
        conn.execute(text("UPDATE news SET publication_status='published' WHERE publication_status IS NULL"))
        conn.execute(text("UPDATE news SET editorial_lock=1 WHERE editorial_lock IS NULL"))
        rows = conn.execute(text("SELECT DISTINCT university FROM news WHERE university IS NOT NULL")).all()
        for (name,) in rows:
            normalized = " ".join(name.split()).casefold()
            conn.execute(text("INSERT OR IGNORE INTO universities(name, normalized_name) VALUES (:name,:normalized)"), {"name":name,"normalized":normalized})
            conn.execute(text("UPDATE news SET university_id=(SELECT id FROM universities WHERE normalized_name=:normalized) WHERE university=:name AND university_id IS NULL"), {"name":name,"normalized":normalized})
def assert_schema_current(engine):
    required = {"news", "universities", "sources", "news_revisions", "ingest_receipts", "analytics_outbox"}
    missing = required - set(inspect(engine).get_table_names())
    if missing: raise RuntimeError("schema_not_current:" + ",".join(sorted(missing)))
if __name__ == "__main__":
    from config import BackendSettings
    bootstrap_database(BackendSettings().database_url)

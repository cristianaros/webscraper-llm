import hashlib
from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, text

from database import make_engine, make_session_factory
from models import MediaAsset, News
from scripts.backfill_media_bytes import backfill_media_bytes
from scripts.migrate_to_postgres import ORDERED_TABLES, migrate_to_postgres, sync_postgres_sequences
from shared.backup import backup_sqlite


def test_legacy_copy_upgrade_backfills_verified_media_and_migrates(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    original = repo / "data/backend/university_news.db"
    if not original.is_file():
        pytest.skip("legacy production database is absent")
    copied = tmp_path / "legacy-copy.db"
    backup_sqlite(original, copied)
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    legacy = make_engine(f"sqlite:///{copied.as_posix()}")
    with legacy.begin() as conn:
        conn.exec_driver_sql("UPDATE alembic_version SET version_num='0005'")
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(media_assets)")}
        if "content_bytes" in cols:
            conn.exec_driver_sql("ALTER TABLE media_assets DROP COLUMN content_bytes")
    legacy.dispose()
    cfg = Config(str(repo / "backend/alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{copied.as_posix()}")
    command.upgrade(cfg, "head")
    source = make_engine(f"sqlite:///{copied.as_posix()}")
    with source.begin() as conn:
        conn.execute(text("UPDATE media_assets SET content_bytes=NULL"))
    with make_session_factory(source)() as db:
        stats = backfill_media_bytes(db, [repo / "data/backend/media"])
        assert stats["missing_or_corrupt"] == 0
        assert stats["backfilled"] == 6
        assert db.query(News).filter_by(publication_status="published").count() == 14
        for asset in db.query(MediaAsset).all():
            assert hashlib.sha256(asset.content_bytes).hexdigest() == asset.sha256
            assert asset.storage_backend == "database"
    source.dispose()

    target = tmp_path / "target.db"
    dest = make_engine(f"sqlite:///{target.as_posix()}")
    from scripts.bootstrap_db import bootstrap_database
    bootstrap_database(f"sqlite:///{target.as_posix()}")
    dest.dispose()
    report = migrate_to_postgres(copied, f"sqlite:///{target.as_posix()}", [repo / "data/backend/media"])
    assert report.table_counts["news"] == 14
    assert report.table_counts["media_assets"] == 6
    assert hashlib.sha256(original.read_bytes()).hexdigest() == original_hash


def test_migration_aborts_and_rolls_back_when_local_media_is_unavailable(tmp_path):
    source_path = tmp_path / "source.db"
    source_engine = make_engine(f"sqlite:///{source_path.as_posix()}")
    from models import Base
    Base.metadata.create_all(source_engine)
    image = b"expected image bytes"
    digest = hashlib.sha256(image).hexdigest()
    with source_engine.begin() as conn:
        conn.execute(text("INSERT INTO media_assets (sha256,storage_key,storage_backend,content_type,width,height,byte_size) VALUES (:h,:k,'local','image/png',1,1,:s)"), {"h": digest, "k": str(tmp_path / "missing.png"), "s": len(image)})
    source_engine.dispose()

    target_path = tmp_path / "destination.db"
    from scripts.bootstrap_db import bootstrap_database
    bootstrap_database(f"sqlite:///{target_path.as_posix()}")
    with pytest.raises(RuntimeError, match=f"media_bytes_unavailable:{digest}"):
        migrate_to_postgres(source_path, f"sqlite:///{target_path.as_posix()}")
    target = make_engine(f"sqlite:///{target_path.as_posix()}")
    with target.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM media_assets")).scalar_one() == 0
        assert conn.execute(text("SELECT COUNT(*) FROM universities")).scalar_one() == 0
    target.dispose()


def test_direct_legacy_migration_backfills_verified_file_without_preprocessing(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    original = repo / "data/backend/university_news.db"
    if not original.is_file():
        pytest.skip("legacy production database is absent")
    copied = tmp_path / "direct-legacy-copy.db"
    backup_sqlite(original, copied)
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    legacy = make_engine(f"sqlite:///{copied.as_posix()}")
    with legacy.begin() as conn:
        conn.exec_driver_sql("UPDATE alembic_version SET version_num='0005'")
        cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(media_assets)")}
        if "content_bytes" in cols:
            conn.exec_driver_sql("ALTER TABLE media_assets DROP COLUMN content_bytes")
    legacy.dispose()
    cfg = Config(str(repo / "backend/alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{copied.as_posix()}")
    command.upgrade(cfg, "head")

    target_path = tmp_path / "direct-target.db"
    from scripts.bootstrap_db import bootstrap_database
    bootstrap_database(f"sqlite:///{target_path.as_posix()}")
    report = migrate_to_postgres(copied, f"sqlite:///{target_path.as_posix()}", [repo / "data/backend/media"])
    assert report.table_counts["media_assets"] == 6
    target = make_engine(f"sqlite:///{target_path.as_posix()}")
    with target.connect() as conn:
        assets = conn.execute(text("SELECT sha256, storage_key, storage_backend, content_bytes FROM media_assets")).mappings().all()
    assert len(assets) == 6
    for asset in assets:
        data = asset["content_bytes"]
        assert data is not None
        assert hashlib.sha256(data).hexdigest() == asset["sha256"]
        assert asset["storage_key"] == f"db://{asset['sha256']}"
        assert asset["storage_backend"] == "database"
    target.dispose()
    assert hashlib.sha256(original.read_bytes()).hexdigest() == original_hash


def test_synthetic_sqlite_backfill_and_order(tmp_path):
    image = b"small-png-fixture"
    digest = hashlib.sha256(image).hexdigest()
    root = tmp_path / "media"
    (root / digest[:2]).mkdir(parents=True)
    (root / digest[:2] / f"{digest}.png").write_bytes(image)
    dbfile = tmp_path / "synthetic.db"
    engine = make_engine(f"sqlite:///{dbfile.as_posix()}")
    from models import Base
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO media_assets (sha256,storage_key,storage_backend,content_type,width,height,byte_size) VALUES (:h,:k,'local','image/png',1,1,:s)"), {"h": digest, "k": "absent.png", "s": len(image)})
    with make_session_factory(engine)() as db:
        assert backfill_media_bytes(db, [root]) == {"already_in_db": 0, "backfilled": 1, "missing_or_corrupt": 0}
    engine.dispose()
    assert ORDERED_TABLES.index("universities") < ORDERED_TABLES.index("sources") < ORDERED_TABLES.index("source_versions")
    assert ORDERED_TABLES.index("news") < ORDERED_TABLES.index("news_revisions") < ORDERED_TABLES.index("news_media_history")


def test_direct_migration_rejects_corrupt_media_bytes(tmp_path):
    expected = b"verified image"
    digest = hashlib.sha256(expected).hexdigest()
    corrupt_root = tmp_path / "corrupt-media"
    candidate = corrupt_root / digest[:2] / f"{digest}.png"
    candidate.parent.mkdir(parents=True)
    candidate.write_bytes(b"corrupt")
    source_path = tmp_path / "corrupt-source.db"
    source = make_engine(f"sqlite:///{source_path.as_posix()}")
    from models import Base
    Base.metadata.create_all(source)
    with source.begin() as conn:
        conn.execute(text("INSERT INTO media_assets (sha256,storage_key,storage_backend,content_type,width,height,byte_size) VALUES (:h,:k,'local','image/png',1,1,:s)"), {"h": digest, "k": str(tmp_path / "not-present.png"), "s": len(expected)})
    source.dispose()
    target_path = tmp_path / "corrupt-target.db"
    from scripts.bootstrap_db import bootstrap_database
    bootstrap_database(f"sqlite:///{target_path.as_posix()}")
    with pytest.raises(RuntimeError, match=f"media_bytes_unavailable:{digest}"):
        migrate_to_postgres(source_path, f"sqlite:///{target_path.as_posix()}", [corrupt_root])
    target = make_engine(f"sqlite:///{target_path.as_posix()}")
    with target.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM media_assets")).scalar_one() == 0
    target.dispose()


def test_postgres_sequence_sync_uses_all_serial_tables():
    executed = []
    class Connection:
        def execute(self, statement, params=None):
            executed.append(str(statement))
    sync_postgres_sequences(Connection())
    assert len(executed) == 5
    assert all("setval(pg_get_serial_sequence" in statement for statement in executed)

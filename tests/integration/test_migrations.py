import sqlite3
import importlib
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect
from backend.scripts.bootstrap_db import bootstrap_database
def test_adopts_legacy_database_and_preserves_ids(tmp_path):
    path=tmp_path/'legacy.db'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE news (id INTEGER PRIMARY KEY,title VARCHAR(255) NOT NULL,summary VARCHAR(500),content TEXT NOT NULL,category VARCHAR(100) NOT NULL,university VARCHAR(200) NOT NULL,author VARCHAR(150),image_url VARCHAR(500),source_url VARCHAR(500),is_featured BOOLEAN,created_at DATETIME,updated_at DATETIME)')
        db.execute('INSERT INTO news(id,title,content,category,university) VALUES(42,?,?,?,?)',('Existing','Original','General','Universidad Prueba'))
    url='sqlite:///'+path.as_posix();bootstrap_database(url);bootstrap_database(url)
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT id,title,content FROM news').fetchone()==(42,'Existing','Original')
        assert db.execute('SELECT COUNT(*) FROM universities').fetchone()[0]==1


def test_alembic_revisions_upgrade_and_downgrade_sqlite_without_losing_legacy_news(tmp_path):
    path = tmp_path / "alembic.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE news (id INTEGER PRIMARY KEY, title VARCHAR(255) NOT NULL, summary VARCHAR(500), content TEXT NOT NULL, category VARCHAR(100) NOT NULL, university VARCHAR(200) NOT NULL, author VARCHAR(150), image_url VARCHAR(500), source_url VARCHAR(500), is_featured BOOLEAN, created_at DATETIME, updated_at DATETIME)")
        db.execute("INSERT INTO news(id, title, content, category, university) VALUES (7, 'Preserved', 'Body', 'General', 'U')")
    engine = create_engine("sqlite:///" + path.as_posix())
    revisions = [importlib.import_module(f"backend.migrations.versions.000{i}_{name}") for i, name in ((1, "legacy_news"), (2, "collection"), (3, "media"), (4, "analytics"), (5, "news_created_at"))]
    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            for migration in revisions:
                migration.upgrade()
            assert connection.exec_driver_sql("SELECT created_at FROM news WHERE id=7").scalar_one() is not None
            for migration in reversed(revisions):
                migration.downgrade()
        assert connection.exec_driver_sql("SELECT id, title FROM news").one() == (7, "Preserved")
        assert {"universities", "news_revisions", "media_assets", "analytics_outbox"} <= set(inspect(connection).get_table_names())

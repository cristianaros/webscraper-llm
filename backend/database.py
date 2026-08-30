import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./university_news.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
logger = logging.getLogger(__name__)


def ensure_schema():
    """Aplica las adiciones pequenas que create_all no agrega a SQLite existente."""
    inspector = inspect(engine)
    if "news" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("news")}
    if "published_at" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE news ADD COLUMN published_at DATETIME"))
        logger.info("Migracion aplicada: news.published_at")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""Database construction; importing this module never opens a database file."""
from __future__ import annotations
from datetime import timezone
from sqlalchemy import create_engine, event
from fastapi import Request
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import DateTime, TypeDecorator

Base = declarative_base()

class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True
    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value

def make_engine(url: str) -> Engine:
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {}, future=True)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def sqlite_pragmas(conn, _):
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON"); cur.execute("PRAGMA journal_mode=WAL"); cur.execute("PRAGMA busy_timeout=5000"); cur.close()
    return engine

def make_session_factory(engine: Engine): return sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

def get_db(request: Request):
    db = request.app.state.session_factory()
    try: yield db
    finally: db.close()

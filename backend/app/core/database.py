import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

logger = logging.getLogger(__name__)

db_url = settings.database_url
sqlite_fallback_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../macrodb.sqlite"))

if db_url.startswith("postgresql"):
    try:
        temp_engine = create_engine(db_url, connect_args={"connect_timeout": 1})
        conn = temp_engine.connect()
        conn.close()
    except Exception:
        logger.warning(f"PostgreSQL at {db_url} unreachable. Falling back to local SQLite at {sqlite_fallback_path}")
        db_url = f"sqlite:///{sqlite_fallback_path}"

engine_args = {}
if db_url.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(db_url, echo=False, future=True, **engine_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from trackreco_platform.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.postgres_dsn, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

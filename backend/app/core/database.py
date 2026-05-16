from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, text
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'aigent.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    agent_id = Column(String(36), nullable=True, index=True)
    content = Column(Text, nullable=False)
    importance = Column(Integer, default=5)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    init_db()
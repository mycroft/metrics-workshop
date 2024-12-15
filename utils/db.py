from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Optional, Any
from contextlib import contextmanager

from model.model import Base
from utils.random import get_random_quantity

class Database:
    def __init__(self, connection_string: str = 'postgresql://demo:demo@localhost:5432/demo'):
        self._engine: Optional[Engine] = None
        self._session_maker: Optional[sessionmaker] = None
        self._connection_string: str = connection_string

    def initialize(self, create_schema: bool = False):
        """Initialize database connection and create schema"""
        self._engine = create_engine(self._connection_string, echo=False)
        self._session_maker = sessionmaker(bind=self._engine)

        if create_schema:
            self.create_schema()

    def create_schema(self) -> None:
        """Create database schema"""
        Base.metadata.create_all(self._engine)

    @contextmanager
    def session(self) -> Session:
        """Get a database session with automatic cleanup"""
        if self._session_maker is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        # Simulate random timeout (keeping existing behavior)
        if get_random_quantity() == 7:
            raise TimeoutError("Database connection timed out")

        session = self._session_maker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        """Clean up database connections"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_maker = None

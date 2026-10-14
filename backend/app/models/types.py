import json
from typing import Optional, List
from sqlalchemy import TypeDecorator, JSON
from pgvector.sqlalchemy import Vector
from backend.app.core.config import settings

class VectorType(TypeDecorator):
    """
    Vector type that adapts to native pgvector Vector(dim) in PostgreSQL,
    and JSON array in SQLite for local testing and development.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int = 768, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        if isinstance(value, list):
            return value
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return list(value)
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return []
        return list(value)

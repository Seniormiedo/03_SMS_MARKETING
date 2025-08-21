"""
Base Model with common fields and configurations
"""

from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from app.core.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """Abstract base model with ID and timestamps"""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"
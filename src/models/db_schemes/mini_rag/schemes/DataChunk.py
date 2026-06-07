from .mini_rag_base import SqlAlchemyBase
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy import Index
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from pgvector.sqlalchemy import Vector


class DataChunk(SqlAlchemyBase):
    __tablename__ = "data_chunks"
    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)

    chunk_text = Column(Text, nullable=False)
    chunk_metadata = Column(JSONB, nullable=True)
    chunk_order = Column(Integer, nullable=False)

    chunk_asset_id = Column(Integer, ForeignKey("assets.asset_id"), nullable=False)
    chunk_project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    chunk_vector = Column(Vector(1536), nullable=True)

    project = relationship("Project", back_populates="data_chunks")
    asset = relationship("Asset", back_populates="data_chunks")

    __table_args__ = (
        Index('ix_data_chunk_asset_id', 'chunk_asset_id'),
        Index('ix_data_chunk_project_id', 'chunk_project_id'),
    )


# FIX: added `score` field with a default of 0.0 so the model can be instantiated
# without requiring a score — previously `score` had no default, so constructing
# RetrievedDocument(text=...) without a score would raise a ValidationError.
# PG_Vector_Provider was constructing it exactly that way, causing a crash.
class RetrievedDocument(BaseModel):
    text: str
    score: float = Field(default=0.0)
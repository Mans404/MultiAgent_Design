from .mini_rag_base import SqlAlchemyBase
from sqlalchemy import Column, ForeignKey, String, Integer, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from sqlalchemy import Index
from sqlalchemy.orm import relationship
class Asset(SqlAlchemyBase):
    __tablename__ = "assets"
    asset_id = Column(Integer, primary_key = True, autoincrement= True)
    asset_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    asset_type = Column(String, nullable=False)
    asset_name = Column(String, nullable=False)
    asset_size = Column(Integer, nullable=False)
    asset_config = Column(JSONB, nullable=True)
    asset_project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)

    project = relationship("Project", back_populates = "assets")
    data_chunks = relationship("DataChunk", back_populates="asset")  

    __table_args__ = (
        Index('ix_asset_project_id', 'asset_project_id'), # Index for faster queries on asset_project_id
    )
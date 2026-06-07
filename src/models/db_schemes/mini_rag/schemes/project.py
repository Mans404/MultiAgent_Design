from .mini_rag_base import SqlAlchemyBase
from sqlalchemy import Column, String, Integer, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
class Project(SqlAlchemyBase):
    __tablename__ = "projects"
    project_id = Column(Integer, primary_key = True, autoincrement= True)
    project_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    created_at = Column(DateTime(timezone = True),server_default=func.now() , nullable=False)
    updated_at = Column(DateTime(timezone = True), onupdate=func.now())
    assets = relationship("Asset", back_populates="project")
    data_chunks = relationship("DataChunk", back_populates = "project")
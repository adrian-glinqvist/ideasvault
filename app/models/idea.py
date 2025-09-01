from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Idea(Base):
    __tablename__ = "ideas"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    tags = Column(Text, nullable=True)  # JSON string of tags
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vote_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    is_anonymous = Column(Boolean, default=False)
    status = Column(String(20), default="active")  # active, flagged, removed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ideas")
    votes = relationship("Vote", back_populates="idea", cascade="all, delete-orphan")
    views = relationship("IdeaView", back_populates="idea", cascade="all, delete-orphan")
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Vote(Base):
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False)
    vote_type = Column(Integer, nullable=False)  # 1 for upvote, -1 for downvote
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="votes")
    idea = relationship("Idea", back_populates="votes")
    
    # Ensure one vote per user per idea
    __table_args__ = (UniqueConstraint('user_id', 'idea_id', name='unique_user_idea_vote'),)

class IdeaView(Base):
    __tablename__ = "idea_views"
    
    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, ForeignKey("ideas.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous views
    ip_address = Column(String(45), nullable=True)  # Store IP for anonymous tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    idea = relationship("Idea", back_populates="views")
    user = relationship("User")
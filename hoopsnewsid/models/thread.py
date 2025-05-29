from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime

from .meta import Base
from .association import thread_tag

class Thread(Base):
    __tablename__ = 'threads'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='threads')
    comments = relationship('Comment', back_populates='thread', cascade='all, delete-orphan')
    
    # Relasi many-to-many dengan Tag
    tags = relationship('Tag', secondary=thread_tag, back_populates='threads')

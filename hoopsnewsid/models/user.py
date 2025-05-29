from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
import datetime
from .meta import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    full_name = Column(String(100))
    bio = Column(String(500))
    avatar_url = Column(String(255))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    articles = relationship('Article', back_populates='author')
    comments = relationship('Comment', back_populates='user')
    threads = relationship('Thread', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

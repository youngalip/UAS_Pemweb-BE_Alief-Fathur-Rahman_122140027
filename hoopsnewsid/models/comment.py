from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
import datetime
from .meta import Base

# models/comment.py
class Comment(Base):
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=True)  # Tambahkan kembali
    thread_id = Column(Integer, ForeignKey('threads.id'), nullable=True)
    parent_id = Column(Integer, ForeignKey('comments.id'), nullable=True)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    user = relationship('User', back_populates='comments')
    article = relationship('Article', back_populates='comments')  # Tambahkan kembali
    thread = relationship('Thread', back_populates='comments')
    replies = relationship(
        'Comment',
        backref=backref('parent', remote_side=[id]),
        cascade='all, delete-orphan'
    )
    
    def __repr__(self):
        return f"<Comment(user_id={self.user_id}, thread_id={self.thread_id})>"

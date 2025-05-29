from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import datetime
from .meta import Base
from .association import article_tag

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    excerpt = Column(String(500))
    content = Column(Text, nullable=False)
    image_url = Column(String(255))
    views = Column(Integer, default=0)
    status = Column(String(20), default='published')  # published, draft
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    published_at = Column(DateTime)
    
    author = relationship('User', back_populates='articles')
    category = relationship('Category', back_populates='articles')
    comments = relationship('Comment', back_populates='article', cascade='all, delete-orphan')
    tags = relationship('Tag', secondary=article_tag, back_populates='articles')
    
    def __repr__(self):
        return f"<Article(title='{self.title}', author_id={self.author_id})>"

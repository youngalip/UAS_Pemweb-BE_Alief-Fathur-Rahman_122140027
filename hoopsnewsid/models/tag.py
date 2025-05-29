from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .meta import Base
from .association import article_tag, thread_tag

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    
    articles = relationship('Article', secondary=article_tag, back_populates='tags')
    threads = relationship('Thread', secondary=thread_tag, back_populates='tags')

    def __repr__(self):
        return f"<Tag(name='{self.name}')>"

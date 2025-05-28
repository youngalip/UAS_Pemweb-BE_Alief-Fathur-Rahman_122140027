from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from .meta import Base

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    
    articles = relationship('Article', back_populates='category')
    
    def __repr__(self):
        return f"<Category(name='{self.name}')>"

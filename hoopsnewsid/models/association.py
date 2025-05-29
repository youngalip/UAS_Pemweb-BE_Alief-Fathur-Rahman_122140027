from sqlalchemy import Column, Integer, ForeignKey, Table
from .meta import Base

# Tabel asosiasi many-to-many antara Thread dan Tag
thread_tag = Table(
    'thread_tag',
    Base.metadata,
    Column('thread_id', Integer, ForeignKey('threads.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

# Tabel asosiasi many-to-many antara Article dan Tag
article_tag = Table(
    'article_tag',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

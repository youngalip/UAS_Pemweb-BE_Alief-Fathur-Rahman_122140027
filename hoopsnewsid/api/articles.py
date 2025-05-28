from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden, HTTPCreated
from ..models import Article, User, Category, Tag
from ..schemas import ArticleSchema, ArticleListSchema
from sqlalchemy import desc
import datetime
import re
import string
import random

def generate_slug(title):
    """Generate a URL-friendly slug from a title."""
    # Convert to lowercase and replace spaces with hyphens
    slug = title.lower().replace(' ', '-')
    # Remove special characters
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Add random suffix to ensure uniqueness
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{slug}-{suffix}"

@view_config(route_name='api_articles', renderer='json', request_method='GET')
def get_articles(request):
    query = request.db.query(Article)
    
    # Filter by category
    category = request.params.get('category')
    if category:
        query = query.join(Article.category).filter(Category.slug == category)
    
    # Filter by tag
    tag = request.params.get('tag')
    if tag:
        query = query.join(Article.tags).filter(Tag.name == tag)
    
    # Filter by author
    author = request.params.get('author')
    if author:
        query = query.join(Article.author).filter(User.username == author)
    
    # Filter by status (only admins can see drafts)
    if request.user and request.user.is_admin:
        status = request.params.get('status', 'published')
        if status != 'all':
            query = query.filter(Article.status == status)
    else:
        query = query.filter(Article.status == 'published')
    
    # Sort by date (default) or views
    sort_by = request.params.get('sort', 'date')
    if sort_by == 'views':
        query = query.order_by(desc(Article.views))
    else:
        query = query.order_by(desc(Article.published_at))
    
    # Pagination
    page = int(request.params.get('page', 1))
    per_page = int(request.params.get('per_page', 10))
    total = query.count()
    
    articles = query.limit(per_page).offset((page - 1) * per_page).all()
    
    schema = ArticleListSchema(many=True)
    return {
        'articles': schema.dump(articles),
        'meta': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    }

@view_config(route_name='api_article', renderer='json', request_method='GET')
def get_article(request):
    article_id = int(request.matchdict['id'])
    article = request.db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        return HTTPNotFound(json={'error': 'Article not found'})
    
    # Check if user can view draft articles
    if article.status == 'draft' and (not request.user or (not request.user.is_admin and request.user.id != article.author_id)):
        return HTTPNotFound(json={'error': 'Article not found'})
    
    # Increment view count
    article.views += 1
    request.db.add(article)
    
    schema = ArticleSchema()
    return schema.dump(article)

@view_config(route_name='api_articles', renderer='json', request_method='POST', permission='create')
def create_article(request):
    if not request.user:
        return HTTPForbidden(json={'error': 'Authentication required'})
    
    try:
        schema = ArticleSchema()
        data = schema.load(request.json_body)
    except Exception as e:
        return HTTPBadRequest(json={'error': str(e)})
    
    # Generate slug from title
    slug = generate_slug(data['title'])
    
    # Create article
    article = Article(
        title=data['title'],
        slug=slug,
        excerpt=data.get('excerpt', ''),
        content=data['content'],
        image_url=data.get('image_url', ''),
        status=data.get('status', 'published'),
        author_id=request.user.id,
        category_id=data.get('category_id'),
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow(),
        published_at=datetime.datetime.utcnow() if data.get('status') != 'draft' else None
    )
    
    # Add tags if provided
    if 'tags' in data and isinstance(data['tags'], list):
        for tag_name in data['tags']:
            tag = request.db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                request.db.add(tag)
                request.db.flush()
            article.tags.append(tag)
    
    request.db.add(article)
    request.db.flush()
    
    return HTTPCreated(json=schema.dump(article))

@view_config(route_name='api_article', renderer='json', request_method='PUT', permission='edit')
def update_article(request):
    article_id = int(request.matchdict['id'])
    article = request.db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        return HTTPNotFound(json={'error': 'Article not found'})
    
    # Check if user can edit the article
    if not request.user.is_admin and request.user.id != article.author_id:
        return HTTPForbidden(json={'error': 'You do not have permission to edit this article'})
    
    try:
        schema = ArticleSchema()
        data = schema.load(request.json_body, partial=True)
    except Exception as e:
        return HTTPBadRequest(json={'error': str(e)})
    
    # Update article fields
    if 'title' in data:
        article.title = data['title']
        # Generate new slug if title changed
        article.slug = generate_slug(data['title'])
    
    if 'excerpt' in data:
        article.excerpt = data['excerpt']
    
    if 'content' in data:
        article.content = data['content']
    
    if 'image_url' in data:
        article.image_url = data['image_url']
    
    if 'status' in data:
        old_status = article.status
        article.status = data['status']
        # Set published_at if article is being published for the first time
        if old_status == 'draft' and data['status'] == 'published' and not article.published_at:
            article.published_at = datetime.datetime.utcnow()
    
    if 'category_id' in data:
        article.category_id = data['category_id']
    
    article.updated_at = datetime.datetime.utcnow()
    
    # Update tags if provided
    if 'tags' in data and isinstance(data['tags'], list):
        # Clear existing tags
        article.tags = []
        
        # Add new tags
        for tag_name in data['tags']:
            tag = request.db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                request.db.add(tag)
                request.db.flush()
            article.tags.append(tag)
    
    request.db.add(article)
    
    return schema.dump(article)

@view_config(route_name='api_article', renderer='json', request_method='DELETE', permission='edit')
def delete_article(request):
    article_id = int(request.matchdict['id'])
    article = request.db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        return HTTPNotFound(json={'error': 'Article not found'})
    
    # Check if user can delete the article
    if not request.user.is_admin and request.user.id != article.author_id:
        return HTTPForbidden(json={'error': 'You do not have permission to delete this article'})
    
    request.db.delete(article)
    
    return {'success': True, 'message': 'Article deleted successfully'}


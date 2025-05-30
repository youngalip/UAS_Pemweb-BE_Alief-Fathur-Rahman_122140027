from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden
from ..models import User, Article, Comment, Category
from sqlalchemy import func, desc
import datetime

@view_config(route_name='api_admin_stats', renderer='json', request_method='GET', permission='admin')
def get_admin_stats(request):
    if not request.user or not request.user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})
    
    # Get total counts
    total_users = request.db.query(func.count(User.id)).scalar()
    total_articles = request.db.query(func.count(Article.id)).scalar()
    total_comments = request.db.query(func.count(Comment.id)).scalar()
    
    # Get total views
    total_views = request.db.query(func.sum(Article.views)).scalar() or 0
    
    # Get recent activities (new users, articles, comments)
    recent_users = request.db.query(User).order_by(User.created_at.desc()).limit(5).all()
    recent_articles = request.db.query(Article).order_by(Article.created_at.desc()).limit(5).all()
    recent_comments = request.db.query(Comment).order_by(Comment.created_at.desc()).limit(5).all()
    
    # Get popular articles
    popular_articles = request.db.query(Article).order_by(Article.views.desc()).limit(5).all()
    
    # Format recent activities
    recent_activities = []
    
    for user in recent_users:
        recent_activities.append({
            'type': 'user_registered',
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.full_name,
                'avatarUrl': user.avatar_url
            },
            'description': f'Pengguna baru mendaftar',
            'time': user.created_at.isoformat()
        })
    
    for article in recent_articles:
        author = article.author
        recent_activities.append({
            'type': 'article_created',
            'user': {
                'id': author.id if author else None,
                'username': author.username if author else 'Unknown',
                'name': author.full_name if author else 'Unknown',
                'avatarUrl': author.avatar_url if author else None
            },
            'description': f'Menambahkan artikel baru "{article.title}"',
            'time': article.created_at.isoformat()
        })

    
    for comment in recent_comments:
        user = comment.user
        article = comment.article
        recent_activities.append({
            'type': 'comment_added',
            'user': {
                'id': user.id if user else None,
                'username': user.username if user else 'Unknown',
                'name': user.full_name if user else 'Unknown',
                'avatarUrl': user.avatar_url if user else None
            },
            'description': f'Mengomentari artikel "{article.title if article else "Unknown"}"',
            'time': comment.created_at.isoformat()
        })

    
    # Sort activities by time
    recent_activities.sort(key=lambda x: x['time'], reverse=True)
    recent_activities = recent_activities[:10]  # Limit to 10 most recent
    
    # Format popular articles
    popular_articles_data = []
    for article in popular_articles:
        author = article.author
        popular_articles_data.append({
            'id': article.id,
            'title': article.title,
            'author': {
                'id': author.id if author else None,
                'name': author.full_name if author else 'Unknown',
                'avatarUrl': author.avatar_url if author else None
            },
            'category': article.category.name if article.category else 'Uncategorized',
            'views': article.views,
            'publishedDate': article.published_at.isoformat() if article.published_at else article.created_at.isoformat()
        })

    
    return {
        'totalUsers': total_users,
        'totalArticles': total_articles,
        'totalComments': total_comments,
        'totalViews': total_views,
        'recentActivities': recent_activities,
        'popularArticles': popular_articles_data
    }

@view_config(route_name='api_admin_users', renderer='json', request_method='GET', permission='admin')
def get_admin_users(request):
    if not request.user or not request.user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})
    
    # Query users
    query = request.db.query(User)
    
    # Filter by search term
    search = request.params.get('search')
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )
    
    # Filter by role
    role = request.params.get('role')
    if role == 'admin':
        query = query.filter(User.is_admin == True)
    elif role == 'user':
        query = query.filter(User.is_admin == False)
    
    # Filter by status
    status = request.params.get('status')
    if status == 'active':
        query = query.filter(User.is_active == True)
    elif status == 'inactive':
        query = query.filter(User.is_active == False)
    
    # Sort by
    sort = request.params.get('sort', 'created_at')
    direction = request.params.get('direction', 'desc')
    
    if sort == 'username':
        query = query.order_by(User.username.desc() if direction == 'desc' else User.username)
    elif sort == 'email':
        query = query.order_by(User.email.desc() if direction == 'desc' else User.email)
    else:  # default to created_at
        query = query.order_by(User.created_at.desc() if direction == 'desc' else User.created_at)
    
    # Pagination
    page = int(request.params.get('page', 1))
    per_page = int(request.params.get('per_page', 10))
    total = query.count()
    
    users = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Format user data
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'avatar_url': user.avatar_url,
            'is_admin': user.is_admin,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        })
    
    return {
        'users': users_data,
        'meta': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    }

@view_config(route_name='api_admin_articles', renderer='json', request_method='GET', permission='admin')
def get_admin_articles(request):
    if not request.user or not request.user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})
    
    # Query articles
    query = request.db.query(Article)
    
    # Filter by search term
    search = request.params.get('search')
    if search:
        query = query.filter(
            (Article.title.ilike(f'%{search}%')) |
            (Article.content.ilike(f'%{search}%'))
        )
    
    # Filter by category
    category_id = request.params.get('category_id')
    if category_id:
        query = query.filter(Article.category_id == category_id)
    
    # Filter by author
    author_id = request.params.get('author_id')
    if author_id:
        query = query.filter(Article.author_id == author_id)
    
    # Filter by status
    status = request.params.get('status')
    if status and status != 'all':
        query = query.filter(Article.status == status)
    
    # Sort by
    sort = request.params.get('sort', 'created_at')
    direction = request.params.get('direction', 'desc')
    
    if sort == 'title':
        query = query.order_by(Article.title.desc() if direction == 'desc' else Article.title)
    elif sort == 'views':
        query = query.order_by(Article.views.desc() if direction == 'desc' else Article.views)
    elif sort == 'published_at':
        query = query.order_by(Article.published_at.desc() if direction == 'desc' else Article.published_at)
    else:  # default to created_at
        query = query.order_by(Article.created_at.desc() if direction == 'desc' else Article.created_at)
    
    # Pagination
    page = int(request.params.get('page', 1))
    per_page = int(request.params.get('per_page', 10))
    total = query.count()
    
    articles = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Format article data
    articles_data = []
    for article in articles:
        articles_data.append({
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'excerpt': article.excerpt,
            'image_url': article.image_url,
            'views': article.views,
            'status': article.status,
            'author': {
                'id': article.author.id,
                'username': article.author.username,
                'name': article.author.full_name,
                'avatarUrl': article.author.avatar_url
            },
            'category': article.category.name if article.category else 'Uncategorized',
            'created_at': article.created_at.isoformat(),
            'published_at': article.published_at.isoformat() if article.published_at else None
        })
    
    return {
        'articles': articles_data,
        'meta': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    }

@view_config(route_name='api_admin_comments', renderer='json', request_method='GET', permission='admin')
def get_admin_comments(request):
    if not request.user or not request.user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})
    
    # Query comments
    query = request.db.query(Comment)
    
    # Filter by search term
    search = request.params.get('search')
    if search:
        query = query.filter(Comment.text.ilike(f'%{search}%'))
    
    # Filter by article
    article_id = request.params.get('article_id')
    if article_id:
        query = query.filter(Comment.article_id == article_id)
    
    # Filter by user
    user_id = request.params.get('user_id')
    if user_id:
        query = query.filter(Comment.user_id == user_id)
    
    # Filter by approval status
    is_approved = request.params.get('is_approved')
    if is_approved is not None:
        is_approved = is_approved.lower() == 'true'
        query = query.filter(Comment.is_approved == is_approved)
    
    # Sort by
    sort = request.params.get('sort', 'created_at')
    direction = request.params.get('direction', 'desc')
    
    if sort == 'created_at':
        query = query.order_by(Comment.created_at.desc() if direction == 'desc' else Comment.created_at)
    
    # Pagination
    page = int(request.params.get('page', 1))
    per_page = int(request.params.get('per_page', 10))
    total = query.count()
    
    comments = query.limit(per_page).offset((page - 1) * per_page).all()
    
    # Format comment data
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'text': comment.text,
            'user': {
                'id': comment.user.id,
                'username': comment.user.username,
                'name': comment.user.full_name,
                'avatarUrl': comment.user.avatar_url
            },
            'article': {
                'id': comment.article.id,
                'title': comment.article.title
            },
            'is_approved': comment.is_approved,
            'created_at': comment.created_at.isoformat()
        })
    
    return {
        'comments': comments_data,
        'meta': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
    }

@view_config(route_name='api_admin_approve_comment', renderer='json', request_method='POST', permission='admin')
def approve_comment(request):
    if not request.user or not request.user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})
    
    comment_id = int(request.matchdict['id'])
    comment = request.db.query(Comment).filter(Comment.id == comment_id).first()
    
    if not comment:
        return HTTPNotFound(json={'error': 'Comment not found'})
    
    comment.is_approved = True
    request.db.add(comment)
    
    return {'success': True, 'message': 'Comment approved successfully'}

@view_config(route_name='api_admin_reject_comment', renderer='json', request_method='POST', permission='admin')
def reject_comment(request):
    if not request.user or not request.user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})
    
    comment_id = int(request.matchdict['id'])
    comment = request.db.query(Comment).filter(Comment.id == comment_id).first()
    
    if not comment:
        return HTTPNotFound(json={'error': 'Comment not found'})
    
    comment.is_approved = False
    request.db.add(comment)
    
    return {'success': True, 'message': 'Comment rejected successfully'}

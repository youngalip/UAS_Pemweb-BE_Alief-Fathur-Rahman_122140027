from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden
from ..models import User, Article, Comment, Category, Thread
from sqlalchemy import func, desc
import datetime
import traceback
import transaction
import logging
import re
from unidecode import unidecode
from ..schemas.article import ArticleSchema

log = logging.getLogger(__name__)

@view_config(route_name='api_admin_stats', renderer='json', request_method='GET', permission='admin')
def get_admin_stats(request):
    if not request.user or not request.user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})
    
    # Get total counts
    total_users = request.db.query(func.count(User.id)).scalar()
    total_articles = request.db.query(func.count(Article.id)).scalar()
    total_comments = request.db.query(func.count(Comment.id)).scalar()
    total_views = request.db.query(func.sum(Article.views)).scalar() or 0
    total_threads = request.db.query(func.count(Thread.id)).scalar() or 0

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
        'totalThreads': total_threads,
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

@view_config(route_name='api_admin_user_delete', request_method='DELETE', permission='admin', renderer='json')
def delete_admin_user(request):
    try:
        user_id_raw = request.matchdict.get('id')
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        return HTTPBadRequest(json={'error': 'Invalid user id'})

    user = request.db.query(User).filter(User.id == user_id).first()
    if not user:
        return HTTPNotFound(json={'error': 'User not found'})

    try:
        with transaction.manager:
            # Hapus data terkait jika perlu (komentar, artikel, dll)
            # Contoh:
            # comments = request.db.query(Comment).filter(Comment.user_id == user_id).all()
            # for comment in comments:
            #     request.db.delete(comment)
            # ...
            
            request.db.delete(user)
    except Exception as e:
        log.exception(f"Error deleting user {user_id}: {e}")
        return HTTPBadRequest(json={'error': str(e)})

    return {'success': True, 'id': user_id}

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

@view_config(route_name='api_admin_articles', renderer='json', request_method='POST', permission='admin')
def create_admin_article(request):
    if not request.user or not request.user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})
    
    try:
        # Log request untuk debugging
        log.info(f"Received article creation request: {request.json_body}")
        
        # Ambil data dari request
        data = request.json_body
        
        # Validasi sederhana tanpa schema
        if not data.get('title'):
            return HTTPBadRequest(json={'error': 'Title is required'})
        if not data.get('content'):
            return HTTPBadRequest(json={'error': 'Content is required'})
        if not data.get('category_id'):
            return HTTPBadRequest(json={'error': 'Category is required'})
        
        # Generate slug jika tidak ada
        slug = data.get('slug')
        if not slug:
            import re
            import string
            import random
            from unidecode import unidecode
            slug_base = unidecode(data['title'].lower())
            slug_base = re.sub(r'[^\w\s-]', '', slug_base)
            slug_base = re.sub(r'[\s_-]+', '-', slug_base)
            slug_base = re.sub(r'^-+|-+$', '', slug_base)
            
            # Pastikan slug unik dengan loop
            slug = slug_base
            suffix_length = 6
            while request.db.query(Article).filter(Article.slug == slug).first():
                suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=suffix_length))
                slug = f"{slug_base}-{suffix}"
        else:
            # Jika slug diberikan, cek keunikan
            if request.db.query(Article).filter(Article.slug == slug).first():
                return HTTPBadRequest(json={'error': 'Slug already exists'})
        
        now = datetime.datetime.utcnow()
        article = Article(
            title=data['title'],
            content=data['content'],
            excerpt=data.get('excerpt', ''),
            image_url=data.get('image_url'),
            status=data.get('status', 'draft'),
            category_id=data.get('category_id'),
            slug=slug,
            author_id=request.user.id,
            created_at=now,
            views=0,
            published_at=now if data.get('status') == 'published' else None
        )
        
        with transaction.manager:
            request.db.add(article)
            request.db.flush()  # Untuk mendapatkan ID artikel
            article_id = article.id
            
            # Jika ada tags, tambahkan
            if 'tags' in data and isinstance(data['tags'], list):
                for tag_name in data['tags']:
                    tag = request.db.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        request.db.add(tag)
                        request.db.flush()
                    article.tags.append(tag)
            
            log.info(f"Article created successfully with ID: {article.id}")
        article = request.db.query(Article).get(article_id)
        # Format response seperti format GET
        response_data = {
            'id': article.id,
            'title': article.title,
            'slug': article.slug,
            'excerpt': article.excerpt,
            'image_url': article.image_url,
            'views': article.views,
            'status': article.status,
            'author': {
                'id': request.user.id,
                'username': request.user.username,
                'name': request.user.full_name,
                'avatarUrl': request.user.avatar_url
            },
            'category': article.category.name if article.category else 'Uncategorized',
            'created_at': article.created_at.isoformat(),
            'published_at': article.published_at.isoformat() if article.published_at else None,
            'tags': [{'id': tag.id, 'name': tag.name} for tag in article.tags]
        }
        
        return response_data
        
    except Exception as e:
        log.exception(f"Error creating article: {str(e)}")
        return HTTPBadRequest(json={'error': str(e)})

@view_config(route_name='api_admin_article_delete', request_method='DELETE', permission='admin', renderer='json')
def delete_admin_article(request):
    try:
        article_id = int(request.matchdict['id'])
        user = request.user

        if not user or not user.is_admin:
            return HTTPForbidden(json={'error': 'Admin access required'})

        with transaction.manager:
            db = request.db
            article = db.query(Article).filter(Article.id == article_id).first()
            if not article:
                return HTTPNotFound(json={'error': 'Article not found'})

            # Hapus semua komentar terkait artikel
            comments = db.query(Comment).filter(Comment.article_id == article_id).all()
            for comment in comments:
                db.delete(comment)

            # Hapus artikel
            db.delete(article)

        return {'success': True, 'id': article_id}

    except Exception as e:
        log.exception(f"Error in delete_admin_article: {str(e)}")
        return HTTPBadRequest(json={'error': str(e)})

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

@view_config(route_name='api_admin_threads', renderer='json', request_method='GET', permission='view')
def get_admin_threads(request):
    print("Admin threads endpoint called")
    print("User:", request.user)
    print("Is admin:", request.user.is_admin if request.user else False)
    if not request.user or not request.user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})
    
    # Ambil semua thread, tidak hanya milik user tertentu
    threads = request.db.query(Thread).order_by(Thread.created_at.desc()).all()
    
    result = []
    for thread in threads:
        # Pastikan thread.user tidak None sebelum mengakses atributnya
        author = {
            'id': None,
            'username': 'Unknown',
            'name': 'Unknown',
            'avatarUrl': None
        }
        
        if thread.user:
            author = {
                'id': thread.user.id,
                'username': thread.user.username,
                'name': thread.user.full_name,
                'avatarUrl': thread.user.avatar_url
            }
        
        # Ambil tags jika ada
        tags = []
        if thread.tags:
            tags = [{'id': tag.id, 'name': tag.name} for tag in thread.tags]
        
        result.append({
            'id': thread.id,
            'title': thread.title,
            'content': thread.content,
            'created_at': thread.created_at.isoformat(),
            'updated_at': thread.updated_at.isoformat() if thread.updated_at else None,
            'author': author,
            'tags': tags,
            'comment_count': len(thread.comments) if hasattr(thread, 'comments') else 0
        })
    
    return result

@view_config(route_name='api_admin_thread_delete', renderer='json', request_method='DELETE', permission='admin')
def delete_admin_thread(request):
    thread_id = int(request.matchdict['id'])
    user = request.user

    if not user or not user.is_admin:
        return HTTPForbidden(json={'error': 'Admin access required'})

    try:
        with transaction.manager:
            db = request.db
            thread = db.query(Thread).filter(Thread.id == thread_id).first()

            if not thread:
                return HTTPNotFound(json={'error': 'Thread not found'})

            db.delete(thread)
    except Exception as e:
        traceback.print_exc()  # Ini akan print error lengkap di console backend
        return HTTPInternalServerError(json={'error': f'Failed to delete thread: {str(e)}'})

    return {'success': True, 'message': 'Thread deleted successfully'}

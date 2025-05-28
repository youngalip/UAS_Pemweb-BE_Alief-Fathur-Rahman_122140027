from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden
from ..models import User, Article
from ..schemas import UserProfileSchema, UserSchema
from ..utils.password import hash_password, verify_password
from sqlalchemy import func

@view_config(route_name='api_user_profile', renderer='json', request_method='GET')
def get_user_profile(request):
    username = request.matchdict['username']
    user = request.db.query(User).filter(User.username == username).first()
    
    if not user:
        return HTTPNotFound(json={'error': 'User not found'})
    
    # Count user articles
    articles_count = request.db.query(func.count(Article.id)).filter(
        Article.author_id == user.id,
        Article.status == 'published'
    ).scalar()
    
    # Create profile data
    profile_data = {
        'id': user.id,
        'username': user.username,
        'full_name': user.full_name,
        'bio': user.bio,
        'avatar_url': user.avatar_url,
        'created_at': user.created_at,
        'articles_count': articles_count,
        'followers_count': 0,  # Placeholder for future implementation
        'following_count': 0,  # Placeholder for future implementation
    }
    
    schema = UserProfileSchema()
    return schema.dump(profile_data)

@view_config(route_name='api_user_articles', renderer='json', request_method='GET')
def get_user_articles(request):
    username = request.matchdict['username']
    user = request.db.query(User).filter(User.username == username).first()
    
    if not user:
        return HTTPNotFound(json={'error': 'User not found'})
    
    # Query user articles
    query = request.db.query(Article).filter(Article.author_id == user.id)
    
    # Only show published articles unless it's the user themselves or an admin
    if not request.user or (request.user.id != user.id and not request.user.is_admin):
        query = query.filter(Article.status == 'published')
    
    # Sort by date
    query = query.order_by(Article.published_at.desc())
    
    # Pagination
    page = int(request.params.get('page', 1))
    per_page = int(request.params.get('per_page', 10))
    total = query.count()
    
    articles = query.limit(per_page).offset((page - 1) * per_page).all()
    
    from ..schemas import ArticleListSchema
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

@view_config(route_name='api_update_profile', renderer='json', request_method='PUT', permission='edit')
def update_profile(request):
    if not request.user:
        return HTTPForbidden(json={'error': 'Authentication required'})
    
    try:
        schema = UserSchema()
        data = schema.load(request.json_body, partial=True)
    except Exception as e:
        return HTTPBadRequest(json={'error': str(e)})
    
    user = request.user
    
    # Update user fields
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    if 'bio' in data:
        user.bio = data['bio']
    
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    
    request.db.add(user)
    
    return schema.dump(user)

@view_config(route_name='api_change_password', renderer='json', request_method='PUT', permission='edit')
def change_password(request):
    if not request.user:
        return HTTPForbidden(json={'error': 'Authentication required'})
    
    try:
        data = request.json_body
        current_password = data.get('current_password')
        new_password = data.get('new_password')
    except Exception as e:
        return HTTPBadRequest(json={'error': str(e)})
    
    if not current_password or not new_password:
        return HTTPBadRequest(json={'error': 'Current password and new password are required'})
    
    user = request.user
    
    # Verify current password
    if not verify_password(user.password_hash, current_password):
        return HTTPBadRequest(json={'error': 'Current password is incorrect'})
    
    # Check new password length
    if len(new_password) < 8:
        return HTTPBadRequest(json={'error': 'New password must be at least 8 characters long'})
    
    # Update password
    user.password_hash = hash_password(new_password)
    request.db.add(user)
    
    return {'success': True, 'message': 'Password changed successfully'}

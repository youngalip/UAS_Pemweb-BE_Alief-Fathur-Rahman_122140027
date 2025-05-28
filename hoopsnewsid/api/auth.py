from pyramid.view import view_config
from pyramid.httpexceptions import HTTPBadRequest, HTTPUnauthorized, HTTPCreated
from ..models import User
from ..schemas import LoginSchema, RegisterSchema
from ..utils.password import hash_password, verify_password
from ..utils.jwt import create_token
import datetime
import re

@view_config(route_name='api_login', renderer='json', request_method='POST')
def login(request):
    try:
        schema = LoginSchema()
        data = schema.load(request.json_body)
    except Exception as e:
        return HTTPBadRequest(json={'error': str(e)})
    
    user = request.db.query(User).filter(User.email == data['email']).first()
    
    if not user or not verify_password(user.password_hash, data['password']):
        return HTTPUnauthorized(json={'error': 'Invalid email or password'})
    
    if not user.is_active:
        return HTTPUnauthorized(json={'error': 'Account is deactivated'})
    
    token = create_token(user.id, request, admin=user.is_admin)
    
    return {
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'avatar_url': user.avatar_url,
            'is_admin': user.is_admin,
        }
    }

@view_config(route_name='api_register', renderer='json', request_method='POST')
def register(request):
    try:
        schema = RegisterSchema()
        data = schema.load(request.json_body)
    except Exception as e:
        return HTTPBadRequest(json={'error': str(e)})
    
    # Check if username is valid
    if not re.match(r'^[a-zA-Z0-9_]+$', data['username']):
        return HTTPBadRequest(json={'error': 'Username can only contain letters, numbers, and underscores'})
    
    # Check if username already exists
    if request.db.query(User).filter(User.username == data['username']).first():
        return HTTPBadRequest(json={'error': 'Username already exists'})
    
    # Check if email already exists
    if request.db.query(User).filter(User.email == data['email']).first():
        return HTTPBadRequest(json={'error': 'Email already exists'})
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=hash_password(data['password']),
        full_name=data.get('full_name', ''),
        created_at=datetime.datetime.utcnow(),
    )
    
    request.db.add(user)
    request.db.flush()  # To get the user ID
    
    token = create_token(user.id, request)
    
    return HTTPCreated(json={
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
        }
    })

@view_config(route_name='api_me', renderer='json', request_method='GET', permission='view')
def get_current_user(request):
    user = request.user
    if not user:
        return HTTPUnauthorized(json={'error': 'Not authenticated'})
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'bio': user.bio,
        'avatar_url': user.avatar_url,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat(),
    }


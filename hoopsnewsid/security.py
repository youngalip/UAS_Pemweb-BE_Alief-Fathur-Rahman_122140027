from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import (
    Authenticated,
    Everyone,
    Allow,
    Deny,
    ALL_PERMISSIONS,
)
from .utils.jwt import decode_token
from .models import User

class JWTAuthenticationPolicy(CallbackAuthenticationPolicy):
    def __init__(self, callback=None):
        self.callback = callback

    def unauthenticated_userid(self, request):
        token = request.headers.get('Authorization', '')
        if token.startswith('Bearer '):
            token = token[7:]  # Remove 'Bearer ' prefix
            payload = decode_token(token, request)
            if payload:
                return payload.get('sub')
        return None

    def remember(self, request, userid, **kw):
        return []

    def forget(self, request):
        return []

def get_user(request):
    user_id = request.unauthenticated_userid
    if user_id is not None:
        return request.db.query(User).filter(User.id == user_id).first()
    return None

class RootFactory:
    __acl__ = [
        (Allow, 'role:admin', ALL_PERMISSIONS),
        (Allow, Authenticated, 'view'),
        (Allow, Everyone, 'view'),
    ]

    def __init__(self, request):
        self.request = request

def includeme(config):
    # Set up authentication
    authn_policy = JWTAuthenticationPolicy(get_user)
    config.set_authentication_policy(authn_policy)
    
    # Set up authorization
    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)
    
    # Set up default permission
    config.set_default_permission('view')
    
    # Set up root factory
    config.set_root_factory(RootFactory)

    # **Tambahkan ini supaya request.user tersedia di view**
    config.add_request_method(get_user, 'user', reify=True)
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.authentication import CallbackAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import Authenticated, Everyone, Allow, ALL_PERMISSIONS

from .utils.jwt import decode_token
from .models import User

class JWTAuthenticationPolicy(CallbackAuthenticationPolicy):
    def __init__(self, callback=None):
        self.callback = callback

    def unauthenticated_userid(self, request):
        token = request.headers.get('Authorization', '')
        if token.startswith('Bearer '):
            token = token[7:]
            payload = decode_token(token, request)
            if payload:
                return payload.get('sub')
        return None

    def remember(self, request, userid, **kw):
        return []

    def forget(self, request):
        return []

# Callback yang mengembalikan list principals (string)
def get_principals(userid, request):
    user = None
    if userid is not None:
        user = request.db.query(User).filter(User.id == userid).first()
    if not user:
        return []
    principals = [f'user:{user.id}']
    if user.is_admin:
        principals.append('role:admin')
    principals.append(Authenticated)
    principals.append(Everyone)
    return principals

# Fungsi untuk request.user (mengembalikan objek User)
def get_user(request):
    userid = request.unauthenticated_userid
    if userid is not None:
        return request.db.query(User).filter(User.id == userid).first()
    return None

def require_auth(view):
    def wrapped_view(context, request):
        if not hasattr(request, 'user') or request.user is None:
            raise HTTPUnauthorized()
        return view(context, request)
    return wrapped_view

class RootFactory:
    __acl__ = [
        (Allow, 'role:admin', ALL_PERMISSIONS),
        (Allow, Authenticated, 'view'),
        (Allow, Everyone, 'view'),
    ]

    def __init__(self, request):
        self.request = request

def includeme(config):
    authn_policy = JWTAuthenticationPolicy(callback=get_principals)
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_default_permission('view')
    config.set_root_factory(RootFactory)

    config.add_request_method(get_user, 'user', reify=True)

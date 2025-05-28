import jwt
import datetime
from pyramid.settings import asbool

def create_token(user_id, request, admin=False):
    """Create a JWT token for a user."""
    settings = request.registry.settings
    secret = settings['jwt.secret']
    expiration = int(settings.get('jwt.expiration', 3600))
    
    payload = {
        'sub': user_id,
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration),
        'admin': admin
    }
    
    return jwt.encode(payload, secret, algorithm='HS256')

def decode_token(token, request):
    """Decode a JWT token."""
    settings = request.registry.settings
    secret = settings['jwt.secret']
    
    try:
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

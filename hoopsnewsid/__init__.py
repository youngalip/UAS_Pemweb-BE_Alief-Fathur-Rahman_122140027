from pyramid.config import Configurator
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import ALL_PERMISSIONS

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings) as config:
        config.include('pyramid_tm')
        
        # Setup database
        config.include('.db')
        
        # Serve static files dari folder 'static' di package 'hoopsnewsid'
        config.add_static_view(name='static', path='hoopsnewsid:static')
        
        # Setup security
        config.include('.security')
        
        # Setup routes
        config.include('.api')
        
        # Scan for views
        config.scan()
    
    return config.make_wsgi_app()

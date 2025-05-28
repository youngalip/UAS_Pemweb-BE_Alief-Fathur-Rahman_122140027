def includeme(config):
    """Configure API routes."""
    
    # Auth routes
    config.add_route('api_login', '/api/auth/login')
    config.add_route('api_register', '/api/auth/register')
    config.add_route('api_me', '/api/auth/me')
    
    # Article routes
    config.add_route('api_articles', '/api/articles')
    config.add_route('api_article', '/api/articles/{id:\d+}')
    config.add_route('categories', '/api/categories')
    config.add_route('api_article_comments', '/api/articles/{id:\d+}/comments')
    
    # Comment routes
    config.add_route('api_comment', '/api/comments/{id:\d+}')
    
    # User routes
    config.add_route('api_user_profile', '/api/users/profile/{username}')
    config.add_route('api_user_articles', '/api/users/{username}/articles')
    config.add_route('api_update_profile', '/api/users/profile')
    config.add_route('api_change_password', '/api/users/password')
    
    # Admin routes
    config.add_route('api_admin_stats', '/api/admin/stats')
    config.add_route('api_admin_users', '/api/admin/users')
    config.add_route('api_admin_articles', '/api/admin/articles')
    config.add_route('api_admin_comments', '/api/admin/comments')
    
    # Include views
    config.scan('.auth')
    config.scan('.articles')
    config.scan('.users')
    config.scan('.comments')
    config.scan('.admin')

    # Tambahkan route untuk approval komentar
    config.add_route('api_admin_approve_comment', '/api/admin/comments/{id:\d+}/approve')
    config.add_route('api_admin_reject_comment', '/api/admin/comments/{id:\d+}/reject')

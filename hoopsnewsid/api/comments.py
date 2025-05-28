from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden, HTTPCreated
from ..models import Comment, Article
from ..schemas import CommentSchema
import datetime

@view_config(route_name='api_article_comments', renderer='json', request_method='GET')
def get_article_comments(request):
    article_id = int(request.matchdict['id'])
    article = request.db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        return HTTPNotFound(json={'error': 'Article not found'})
    
    # Get top-level comments (no parent)
    comments = request.db.query(Comment).filter(
        Comment.article_id == article_id,
        Comment.parent_id == None,
        Comment.is_approved == True
    ).order_by(Comment.created_at.desc()).all()
    
    schema = CommentSchema(many=True)
    return schema.dump(comments)

@view_config(route_name='api_article_comments', renderer='json', request_method='POST', permission='create')
def add_comment(request):
    if not request.user:
        return HTTPForbidden(json={'error': 'Authentication required'})
    
    article_id = int(request.matchdict['id'])
    article = request.db.query(Article).filter(Article.id == article_id).first()
    
    if not article:
        return HTTPNotFound(json={'error': 'Article not found'})
    
    try:
        schema = CommentSchema()
        data = schema.load(request.json_body)
    except Exception as e:
        return HTTPBadRequest(json={'error': str(e)})
    
    # Create comment
    comment = Comment(
        text=data['text'],
        user_id=request.user.id,
        article_id=article_id,
        parent_id=data.get('parent_id'),
        is_approved=True,  # Auto-approve for now
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    
    request.db.add(comment)
    request.db.flush()
    
    return HTTPCreated(json=schema.dump(comment))

@view_config(route_name='api_comment', renderer='json', request_method='PUT', permission='edit')
def update_comment(request):
    comment_id = int(request.matchdict['id'])
    comment = request.db.query(Comment).filter(Comment.id == comment_id).first()
    
    if not comment:
        return HTTPNotFound(json={'error': 'Comment not found'})
    
    # Check if user can edit the comment
    if not request.user.is_admin and request.user.id != comment.user_id:
        return HTTPForbidden(json={'error': 'You do not have permission to edit this comment'})
    
    try:
        schema = CommentSchema()
        data = schema.load(request.json_body, partial=True)
    except Exception as e:
        return HTTPBadRequest(json={'error': str(e)})
    
    # Update comment
    if 'text' in data:
        comment.text = data['text']
    
    comment.updated_at = datetime.datetime.utcnow()
    request.db.add(comment)
    
    return schema.dump(comment)

@view_config(route_name='api_comment', renderer='json', request_method='DELETE', permission='edit')
def delete_comment(request):
    comment_id = int(request.matchdict['id'])
    comment = request.db.query(Comment).filter(Comment.id == comment_id).first()
    
    if not comment:
        return HTTPNotFound(json={'error': 'Comment not found'})
    
    # Check if user can delete the comment
    if not request.user.is_admin and request.user.id != comment.user_id:
        return HTTPForbidden(json={'error': 'You do not have permission to delete this comment'})
    
    request.db.delete(comment)
    
    return {'success': True, 'message': 'Comment deleted successfully'}

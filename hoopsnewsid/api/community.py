from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden, HTTPCreated
from sqlalchemy.orm import joinedload
from sqlalchemy import desc
import datetime
from marshmallow import ValidationError

from ..models import Thread, Comment, User, Tag
from ..schemas.thread import ThreadSchema, ThreadDetailSchema
from ..schemas.comment import CommentSchema
from ..security import require_auth

@view_config(route_name='api_threads', renderer='json', request_method='GET')
def get_threads(context, request):
    db = request.db
    threads = db.query(Thread).options(
        joinedload(Thread.user)
    ).order_by(desc(Thread.created_at)).all()
    for thread in threads:
        thread.comment_count = len(thread.comments)
    return ThreadSchema(many=True).dump(threads)


@view_config(route_name='api_thread_detail', renderer='json', request_method='GET')
def get_thread_detail(context, request):
    thread_id = int(request.matchdict['id'])
    db = request.db
    thread = db.query(Thread).options(
        joinedload(Thread.user),
        joinedload(Thread.comments).joinedload(Comment.user)
    ).filter(Thread.id == thread_id).first()
    if not thread:
        return HTTPNotFound(json={'error': 'Thread not found'})
    return ThreadDetailSchema().dump(thread)


@view_config(route_name='api_threads', renderer='json', request_method='POST')
@require_auth
def create_thread(context, request):
    import transaction
    
    user = request.user
    thread_data = request.json_body
    
    # Validasi data input di luar transaksi
    schema = ThreadSchema()
    try:
        validated_data = schema.load(thread_data)
    except ValidationError as e:
        return HTTPBadRequest(json={'error': e.messages})
    
    # Gunakan transaksi manual dengan with block
    with transaction.manager:
        db = request.db
        new_thread = Thread(
            title=validated_data['title'],
            content=validated_data['content'],
            user_id=user.id,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        
        db.add(new_thread)
        
        # Proses tags jika ada
        if 'tags' in validated_data and validated_data['tags']:
            for tag_name in validated_data['tags']:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                new_thread.tags.append(tag)
    
    # Buat response sederhana tanpa datetime
    response_data = {
        'success': True,
        'message': 'Thread created successfully',
        'title': validated_data['title'],
        'content': validated_data['content']
    }
    
    return HTTPCreated(json=response_data)

# Update Thread
@view_config(route_name='api_thread_detail', renderer='json', request_method='PUT')
@require_auth
def update_thread(context, request):
    import transaction
    
    thread_id = int(request.matchdict['id'])
    user = request.user
    thread_data = request.json_body
    
    schema = ThreadSchema()
    try:
        validated_data = schema.load(thread_data, partial=True)
    except ValidationError as e:
        return HTTPBadRequest(json={'error': e.messages})
    
    with transaction.manager:
        db = request.db
        thread = db.query(Thread).filter(Thread.id == thread_id).first()
        
        if not thread:
            return HTTPNotFound(json={'error': 'Thread not found'})
            
        if thread.user_id != user.id and not user.is_admin:
            return HTTPForbidden(json={'error': 'You can only update your own threads'})
            
        if 'title' in validated_data:
            thread.title = validated_data['title']
            
        if 'content' in validated_data:
            thread.content = validated_data['content']
            
        if 'tags' in validated_data:
            # Clear existing tags
            thread.tags = []
            for tag_name in validated_data['tags']:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                thread.tags.append(tag)
                
        thread.updated_at = datetime.datetime.utcnow()
    
    # Buat response sederhana
    response_data = {
        'success': True,
        'message': 'Thread updated successfully',
        'title': thread.title,
        'content': thread.content
    }
    
    return response_data



@view_config(route_name='api_thread_detail', renderer='json', request_method='DELETE')
@require_auth
def delete_thread(context, request):
    import transaction
    
    thread_id = int(request.matchdict['id'])
    user = request.user
    
    # Gunakan transaksi manual dengan with block
    with transaction.manager:
        db = request.db
        thread = db.query(Thread).filter(Thread.id == thread_id).first()
        
        if not thread:
            return HTTPNotFound(json={'error': 'Thread not found'})
            
        if thread.user_id != user.id and not user.is_admin:
            return HTTPForbidden(json={'error': 'You can only delete your own threads'})
            
        db.delete(thread)
        # transaction.commit() akan dipanggil otomatis di akhir blok with
    
    # Buat response sederhana
    response_data = {
        'success': True,
        'message': 'Thread deleted successfully'
    }
    
    return response_data

# Add Comment
@view_config(route_name='api_thread_comments', renderer='json', request_method='POST')
@require_auth
def add_comment(context, request):
    import transaction
    
    thread_id = int(request.matchdict['id'])
    user = request.user
    comment_data = request.json_body
    
    schema = CommentSchema()
    try:
        validated_data = schema.load(comment_data)
    except ValidationError as e:
        return HTTPBadRequest(json={'error': e.messages})
    
    with transaction.manager:
        db = request.db
        thread = db.query(Thread).filter(Thread.id == thread_id).first()
        
        if not thread:
            return HTTPNotFound(json={'error': 'Thread not found'})
            
        new_comment = Comment(
            content=validated_data['content'],
            user_id=user.id,
            thread_id=thread_id,
            parent_id=validated_data.get('parent_id'),
            is_approved=True,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        
        db.add(new_comment)
    
    # Buat response sederhana
    response_data = {
        'success': True,
        'message': 'Comment added successfully',
        'content': new_comment.content
    }
    
    return HTTPCreated(json=response_data)

# Delete Comment
@view_config(route_name='api_comment_detail', renderer='json', request_method='DELETE')
@require_auth
def delete_comment(context, request):
    import transaction
    
    thread_id = int(request.matchdict['thread_id'])
    comment_id = int(request.matchdict['comment_id'])
    user = request.user
    
    with transaction.manager:
        db = request.db
        comment = db.query(Comment).filter(
            Comment.id == comment_id,
            Comment.thread_id == thread_id
        ).first()
        
        if not comment:
            return HTTPNotFound(json={'error': 'Comment not found'})
            
        if comment.user_id != user.id and not user.is_admin:
            return HTTPForbidden(json={'error': 'You can only delete your own comments'})
            
        db.delete(comment)
    
    return {'success': True, 'message': 'Comment deleted successfully'}

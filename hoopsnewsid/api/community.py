from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest, HTTPForbidden, HTTPCreated
from sqlalchemy.orm import joinedload
from sqlalchemy import desc
import datetime
from marshmallow import ValidationError
import transaction

from ..models import Thread, Comment, User, Tag
from ..schemas.thread import ThreadSchema, ThreadDetailSchema
from ..schemas.comment import CommentSchema
from ..security import require_auth

@view_config(route_name='api_threads', renderer='json', request_method='GET')
def get_threads(request):
    db = request.db
    threads = db.query(Thread).options(
        joinedload(Thread.user),
        joinedload(Thread.tags)
    ).order_by(desc(Thread.created_at)).all()
    
    for thread in threads:
        thread.comment_count = len(thread.comments)
    
    return ThreadSchema(many=True).dump(threads)


@view_config(route_name='api_thread_detail', renderer='json', request_method='GET')
def get_thread_detail(request):
    thread_id = int(request.matchdict['id'])
    db = request.db
    thread = db.query(Thread).options(
        joinedload(Thread.user),
        joinedload(Thread.comments).joinedload(Comment.user),
        joinedload(Thread.tags)
    ).filter(Thread.id == thread_id).first()
    
    if not thread:
        return HTTPNotFound(json={'error': 'Thread not found'})
    
    return ThreadDetailSchema().dump(thread)


@view_config(route_name='api_threads', renderer='json', request_method='POST')
@require_auth
def create_thread(context, request):
    user = request.user
    thread_data = request.json_body

    schema = ThreadSchema()
    try:
        validated_data = schema.load(thread_data)
    except ValidationError as e:
        return HTTPBadRequest(json={'error': e.messages})

    # Simpan data untuk response
    title = validated_data['title']
    content = validated_data['content']
    tag_names = validated_data.get('tags', [])

    with transaction.manager:
        db = request.db
        new_thread = Thread(
            title=title,
            content=content,
            user_id=user.id,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        
        db.add(new_thread)
        
        # Proses tags
        for tag_name in tag_names:
            # Pastikan tag_name adalah string sederhana, bukan representasi objek
            if tag_name.startswith('<Tag(') and tag_name.endswith(')>'):
                # Ekstrak nama tag dari representasi string
                import re
                match = re.search(r"name='([^']+)'", tag_name)
                if match:
                    tag_name = match.group(1)
            
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
            new_thread.tags.append(tag)

    # Buat response sederhana
    response_data = {
        'success': True,
        'message': 'Thread created successfully',
        'title': title,
        'content': content,
        'tags': tag_names,
        'user': {
            'id': user.id,
            'username': user.username,
            'avatar_url': getattr(user, 'avatar_url', None)
        },
        'created_at': datetime.datetime.utcnow().isoformat()
    }
    
    return HTTPCreated(json=response_data)


@view_config(route_name='api_thread_detail', renderer='json', request_method='PUT')
@require_auth
def update_thread(context, request):
    thread_id = int(request.matchdict['id'])
    user = request.user
    thread_data = request.json_body
    
    schema = ThreadSchema()
    try:
        validated_data = schema.load(thread_data, partial=True)
    except ValidationError as e:
        return HTTPBadRequest(json={'error': e.messages})
    
    # Simpan data yang diupdate untuk response
    updated_title = validated_data.get('title')
    updated_content = validated_data.get('content')
    updated_tags = validated_data.get('tags', [])
    
    # Bersihkan tag names sebelum diproses
    cleaned_tags = []
    for tag_name in updated_tags:
        # Pastikan tag_name adalah string sederhana, bukan representasi objek
        if isinstance(tag_name, str) and tag_name.startswith('<Tag(') and tag_name.endswith(')>'):
            # Ekstrak nama tag dari representasi string
            import re
            match = re.search(r"name='([^']+)'", tag_name)
            if match:
                tag_name = match.group(1)
        cleaned_tags.append(tag_name)
    
    with transaction.manager:
        db = request.db
        thread = db.query(Thread).filter(Thread.id == thread_id).first()
        
        if not thread:
            return HTTPNotFound(json={'error': 'Thread not found'})
            
        if thread.user_id != user.id and not user.is_admin:
            return HTTPForbidden(json={'error': 'You can only update your own threads'})
        
        # Simpan nilai asli jika tidak diupdate
        if updated_title is None:
            updated_title = thread.title
        else:
            thread.title = updated_title
            
        if updated_content is None:
            updated_content = thread.content
        else:
            thread.content = updated_content
            
        if 'tags' in validated_data:
            # Clear existing tags
            thread.tags = []
            for tag_name in cleaned_tags:  # Gunakan cleaned_tags yang sudah dibersihkan
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                thread.tags.append(tag)
                
        thread.updated_at = datetime.datetime.utcnow()
    
    # Buat response sederhana dengan data yang sudah disimpan
    response_data = {
        'success': True,
        'message': 'Thread updated successfully',
        'id': thread_id,
        'title': updated_title,
        'content': updated_content,
        'tags': cleaned_tags  # Gunakan cleaned_tags di response
    }
    
    return response_data

@view_config(route_name='api_thread_detail', renderer='json', request_method='DELETE')
@require_auth
def delete_thread(context, request):
    thread_id = int(request.matchdict['id'])
    user = request.user
    
    with transaction.manager:
        db = request.db
        thread = db.query(Thread).filter(Thread.id == thread_id).first()
        
        if not thread:
            return HTTPNotFound(json={'error': 'Thread not found'})
            
        if thread.user_id != user.id and not user.is_admin:
            return HTTPForbidden(json={'error': 'You can only delete your own threads'})
            
        db.delete(thread)
    
    return {'success': True, 'message': 'Thread deleted successfully'}


@view_config(route_name='api_thread_comments', renderer='json', request_method='POST')
@require_auth
def add_comment(context, request):
    thread_id = int(request.matchdict['id'])
    user = request.user
    comment_data = request.json_body
    
    schema = CommentSchema()
    try:
        # Tambahkan thread_id ke data sebelum validasi jika tidak ada
        if 'thread_id' not in comment_data:
            comment_data['thread_id'] = thread_id
            
        validated_data = schema.load(comment_data)
    except ValidationError as e:
        return HTTPBadRequest(json={'error': e.messages})
    
    # Simpan content untuk response
    comment_content = validated_data['content']
    
    with transaction.manager:
        db = request.db
        thread = db.query(Thread).filter(Thread.id == thread_id).first()
        
        if not thread:
            return HTTPNotFound(json={'error': 'Thread not found'})
            
        new_comment = Comment(
            content=comment_content,
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
        'id': None,  # ID akan diisi setelah commit
        'content': comment_content,
        'user': {
            'id': user.id,
            'username': user.username,
            'avatar_url': getattr(user, 'avatar_url', None)
        },
        'created_at': datetime.datetime.utcnow().isoformat()
    }
    
    return HTTPCreated(json=response_data)


@view_config(route_name='api_comment_detail', renderer='json', request_method='DELETE')
@require_auth
def delete_comment(context, request):
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

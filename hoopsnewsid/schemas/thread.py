from marshmallow import Schema, fields, validate, INCLUDE
from .user import UserSchema

class ThreadSchema(Schema):
    class Meta:
        # Izinkan field tambahan yang tidak didefinisikan dalam schema
        unknown = INCLUDE
    
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    content = fields.Str(required=True, validate=validate.Length(min=10))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    user_id = fields.Int(dump_only=True)
    user = fields.Nested(UserSchema, dump_only=True)
    comment_count = fields.Int(dump_only=True)
    
    # Untuk input - list string tag names
    tags = fields.List(fields.Str(), required=False)
    
    # Untuk output - nested Tag objects (gunakan nama berbeda untuk menghindari konflik)
    tags_data = fields.Nested('TagSchema', many=True, dump_only=True, attribute="tags")

class ThreadDetailSchema(ThreadSchema):
    comments = fields.Nested('CommentSchema', many=True, dump_only=True)
    # Jika ingin tags juga muncul di detail:
    # tags = fields.Nested('TagSchema', many=True, dump_only=True)

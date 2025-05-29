from marshmallow import Schema, fields, validate

class CommentSchema(Schema):
    id = fields.Int(dump_only=True)
    content = fields.Str(required=True, validate=validate.Length(min=1))
    user_id = fields.Int(dump_only=True)
    thread_id = fields.Int(required=True)
    parent_id = fields.Int(allow_none=True)
    is_approved = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    # Nested fields
    user = fields.Nested('UserSchema', only=('id', 'username', 'full_name', 'avatar_url'), dump_only=True)
    replies = fields.List(fields.Nested('self', exclude=('replies',)), dump_only=True)

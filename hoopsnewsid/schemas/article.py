from marshmallow import Schema, fields, validate

class ArticleSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    slug = fields.Str(dump_only=True)
    excerpt = fields.Str(validate=validate.Length(max=500))
    content = fields.Str(required=True)
    image_url = fields.Str()
    views = fields.Int(dump_only=True)
    status = fields.Str(validate=validate.OneOf(['published', 'draft']))
    author_id = fields.Int(dump_only=True)
    category_id = fields.Int()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    published_at = fields.DateTime(dump_only=True)
    
    # Nested fields
    author = fields.Nested('UserSchema', only=('id', 'username', 'full_name', 'avatar_url'), dump_only=True)
    category = fields.Nested('CategorySchema', only=('id', 'name', 'slug'), dump_only=True)
    tags = fields.List(fields.Nested('TagSchema', only=('id', 'name')), dump_only=True)

class ArticleListSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    slug = fields.Str()
    excerpt = fields.Str()
    image_url = fields.Str()
    views = fields.Int()
    status = fields.Str()
    author_id = fields.Int()
    category_id = fields.Int()
    published_at = fields.DateTime()
    
    # Nested fields
    author = fields.Nested('UserSchema', only=('id', 'username', 'full_name', 'avatar_url'))
    category = fields.Nested('CategorySchema', only=('id', 'name', 'slug'))

class TagSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))

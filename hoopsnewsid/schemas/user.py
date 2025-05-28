from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)
    full_name = fields.Str()
    bio = fields.Str()
    avatar_url = fields.Str()
    is_admin = fields.Bool(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class UserProfileSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    full_name = fields.Str()
    bio = fields.Str()
    avatar_url = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    articles_count = fields.Int(dump_only=True)
    followers_count = fields.Int(dump_only=True)
    following_count = fields.Int(dump_only=True)

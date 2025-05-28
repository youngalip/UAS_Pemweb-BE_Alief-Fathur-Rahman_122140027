from marshmallow import Schema, fields, validate, validates, ValidationError

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    full_name = fields.Str()

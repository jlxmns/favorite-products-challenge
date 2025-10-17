from ninja import ModelSchema, Schema

from api.models import AuthToken
from core.models import User


class UserSchemaOut(ModelSchema):
    class Meta:
        model = User
        fields = ["name", "email"]


class AuthTokenOut(ModelSchema):
    class Meta:
        model = AuthToken
        fields = ["key"]


class LoginSchemaIn(Schema):
    email: str
    password: str

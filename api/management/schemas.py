from ninja import ModelSchema

from core.models import User


class UserBaseSchema(ModelSchema):
    class Meta:
        model = User
        fields = ["id", "name", "email"]


class UserSchemaIn(ModelSchema):
    class Meta:
        model = User
        fields = [
            "name", "email", "password"
        ]


class UserSchemaOut(UserBaseSchema):
    token: str

    @staticmethod
    def resolve_token(obj):
        return obj.token


class UserSchemaUpdate(ModelSchema):
    class Meta:
        model = User
        fields = ["name", "email", "password"]
        fields_optional = '__all__'

from django.db import IntegrityError
from ninja import Router, Form
from ninja.pagination import PageNumberPagination, paginate

from api.management.errors import user_errors, user_create_errors, user_update_errors
from api.management.schemas import UserSchemaIn, UserSchemaOut, UserBaseSchema, UserSchemaUpdate
from api.models import AuthToken
from core.models import User

management_router = Router()

@management_router.get("/user/list", response={200: list[UserBaseSchema]})
@paginate(PageNumberPagination, page_size=20)
def get_user_list(request):
    return User.objects.all().order_by("name")

@management_router.post("/user", response={201: UserSchemaOut, **user_create_errors})
def create_user(request, payload: UserSchemaIn):
    try:
        user = User.objects.create_user(email=payload.email, name=payload.name, password=payload.password)
    except IntegrityError:
        return 400, user_create_errors[400].EmailInUse.value

    AuthToken.objects.create(user=user)
    return 201, user

@management_router.get("/user/{user_id}", response={200: UserBaseSchema, **user_errors})
def get_user(request, user_id: int):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return 400, user_errors[400].UserNotFound.value

    return 200, user

@management_router.put("/user/{user_id}", response={200: UserSchemaOut, **user_update_errors})
def update_user(request, user_id: int, payload: UserSchemaUpdate):
    updated_fields = payload.dict(exclude_unset=True)
    password = updated_fields.pop("password", None)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return 400, user_update_errors[400].UserNotFound.value

    email_check = User.objects.filter(email=payload.email).first()
    if email_check:
        return 400, user_update_errors[400].EmailInUse.value

    for attr, value in updated_fields.items():
        setattr(user, attr, value)

    if password:
        user.set_password(password)

    user.save()

    return 200, user

@management_router.delete("/user/{user_id}", response={204: None, **user_errors})
def delete_user(request, user_id: int):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return 400, user_errors[400].UserNotFound.value

    user.delete()

    return 204, None

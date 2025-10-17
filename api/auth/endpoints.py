from django.contrib.auth.hashers import check_password
from ninja import Router
from ninja.errors import HttpError

from api.auth.schemas import UserSchemaOut, LoginSchemaIn
from api.models import AuthToken
from core.models import User

auth_router = Router()

@auth_router.get('/user', response={200: UserSchemaOut, 401: dict})
def get_auth_user(request):
    user = request.auth
    if not user:
        return 401, {"error": "Invalid or missing token"}

    return 200, user

@auth_router.get('/token', response={201: str, 401: dict})
def get_auth_token(request):
    user = request.auth
    if not user:
        return 401, {"error": "Invalid or missing token"}

    return 201, user.token

@auth_router.post("/login", response={200: dict, 401: dict}, auth=None)
def login(request, payload: LoginSchemaIn):
    try:
        user = User.objects.get(email=payload.email)

        if not check_password(payload.password, user.password):
            return 401, {"error": "Invalid email or password."}

        token, created = AuthToken.objects.get_or_create(user=user)

        return 200, {"token": token.key}

    except User.DoesNotExist:
        return 401, {"error": "Invalid email or password."}

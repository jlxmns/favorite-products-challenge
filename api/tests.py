from django.test import Client

from api.models import AuthToken
from core.models import User


class TestHelper:
    @classmethod
    def create_admin_user(cls, name="n", email="e@e.com", password="abc"):
        user = User.objects.create_user(name=name, email=email, password=password, role=User.Role.ADMIN)
        token = AuthToken.objects.create(user=user)
        return user, token

    @classmethod
    def create_customer_user(cls, name="n", email="e@e.com", password="abc"):
        user = User.objects.create_user(name=name, email=email, password=password, role=User.Role.CUSTOMER)
        token = AuthToken.objects.create(user=user)
        return user, token

    @classmethod
    def client_from_user(cls, user):
        client = Client(headers={"X-API-Key": user.token})
        return client
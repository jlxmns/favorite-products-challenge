from ninja.security import APIKeyHeader
from decimal import Decimal

from api.models import AuthToken
from core.models import Product


# AUTH

class ApiKey(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        try:
            token = AuthToken.objects.select_related("user").get(key=key)
            return token.user
        except AuthToken.DoesNotExist:
            return None


class AdminApiKey(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        try:
            token = AuthToken.objects.select_related("user").get(key=key)
            user = token.user
            if user.role == user.Role.ADMIN:
                return user
        except AuthToken.DoesNotExist:
            pass
        return None


# Helper Functions

def create_product_from_api_data(data):
    """
    Create and save a Product instance from external API JSON data.
    """
    product = Product(
        api_id=data["id"],
        title=data["title"],
        price=Decimal(str(data["price"])),
        description=data["description"],
        category=data["category"],
        image=data["image"],
        rating_rate=Decimal(str(data["rating"]["rate"])) if data.get("rating") and data["rating"].get("rate") else None,
        rating_count=data["rating"]["count"] if data.get("rating") and data["rating"].get("count") else None,
    )
    product.save()
    return product

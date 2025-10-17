import requests
from django.db import IntegrityError
from ninja import Router
from ninja.pagination import PageNumberPagination, paginate

from api.common.schemas import ProductSchemaOut
from api.product_api import ProductAPIClient
from api.utils import create_product_from_api_data
from core.models import Product, FavoriteProducts

common_router = Router()

@common_router.post("/favorites/{p_id}", response={201: ProductSchemaOut, 400: dict})
def add_favorite(request, p_id: int):
    product = Product.objects.filter(api_id=p_id).first()
    client = ProductAPIClient()

    if not product:
        try:
            product_data = client.get_product(p_id)
            product = create_product_from_api_data(product_data)
        except (requests.RequestException, KeyError, ValueError) as _:
            return 400, {"error": "Product not found or could not be fetched from the API."}
    try:
        FavoriteProducts.objects.create(user=request.auth, product=product)
    except IntegrityError:
        return 400, {"error": "The product selected is already on user's favorites."}

    return 201, product

@common_router.post("/favorites/{p_id}/delete", response={204: None, 400: str})
def delete_favorite(request, p_id: int):
    product_in_favorite = FavoriteProducts.objects.filter(user=request.auth, product__api_id=p_id).first()

    if not product_in_favorite:
        return 400, "This product is not on your favorites."

    product_in_favorite.delete()
    return 204, None

@common_router.get("/favorites", response={200: list[ProductSchemaOut]})
@paginate(PageNumberPagination, page_size=20)
def get_favorites(request):
    return Product.objects.filter(favoriteproducts__user=request.auth).order_by("date_created")

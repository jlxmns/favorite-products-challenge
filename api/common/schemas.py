from ninja import ModelSchema

from core.models import Product


class ProductSchemaOut(ModelSchema):
    class Meta:
        model = Product
        fields = ['api_id', 'title', 'image', 'price', 'rating_rate', 'rating_count']

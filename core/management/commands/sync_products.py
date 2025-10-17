from django.core.management.base import BaseCommand
from decimal import Decimal
import requests
from core.models import Product


class Command(BaseCommand):
    help = 'Sync products from external API and update local database'

    def handle(self, *args, **options):
        self.stdout.write('Fetching products from API...')

        try:
            response = requests.get('https://fakestoreapi.com/products')
            api_products = response.json()
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Failed to fetch products: {e}'))
            return

        updated_count = 0
        skipped_count = 0

        for product_data in api_products:
            api_id = product_data['id']

            try:
                product = Product.objects.get(api_id=api_id)

                has_changes = (
                        product.title != product_data['title'] or
                        product.price != Decimal(str(product_data['price'])) or
                        product.description != product_data['description'] or
                        product.category != product_data['category'] or
                        product.image != product_data['image']
                )

                if has_changes:
                    product.title = product_data['title']
                    product.price = Decimal(str(product_data['price']))
                    product.description = product_data['description']
                    product.category = product_data['category']
                    product.image = product_data['image']

                    if product_data.get('rating'):
                        product.rating_rate = Decimal(str(product_data['rating']['rate']))
                        product.rating_count = product_data['rating']['count']

                    product.save()
                    updated_count += 1
                    self.stdout.write(f'Updated product: {product.title}')
                else:
                    skipped_count += 1

            except Product.DoesNotExist:
                skipped_count += 1
                continue

        self.stdout.write(self.style.SUCCESS(
            f'\nSync complete! Updated: {updated_count}, Skipped: {skipped_count}'
        ))

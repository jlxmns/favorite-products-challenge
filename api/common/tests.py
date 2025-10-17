import requests
from django.test import TestCase, Client
from decimal import Decimal

from api.product_api import ProductAPIClient
from api.tests import TestHelper
from api.utils import create_product_from_api_data
from core.models import Product, FavoriteProducts
from unittest.mock import patch, Mock


class CommonTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user, _ = TestHelper.create_customer_user()
        self.client = TestHelper.client_from_user(self.user)


class AddFavoriteTests(CommonTestCase):
    def setUp(self):
        super().setUp()
        self.url_template = "/api/common/favorites/{}"

    def test_add_favorite_new_product_success(self):
        """Test successfully adding a new product to favorites that doesn't exist locally"""
        p_id = 1
        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 201)
        response_data = response.json()

        self.assertIn('api_id', response_data)
        self.assertIn('title', response_data)
        self.assertIn('price', response_data)
        self.assertIn('image', response_data)

        product_exists = Product.objects.filter(api_id=p_id).exists()
        self.assertTrue(product_exists)

        favorite_exists = FavoriteProducts.objects.filter(
            user=self.user,
            product__api_id=p_id
        ).exists()
        self.assertTrue(favorite_exists)

    def test_add_favorite_existing_product(self):
        """Test adding an existing local product to favorites"""
        p_id = 2
        product_data = ProductAPIClient().get_product(p_id)
        product = create_product_from_api_data(product_data)

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 201)

        favorite_exists = FavoriteProducts.objects.filter(
            user=self.user,
            product=product
        ).exists()
        self.assertTrue(favorite_exists)

    def test_add_favorite_duplicate(self):
        """Test that adding the same product twice returns error"""
        p_id = 3

        response1 = self.client.post(self.url_template.format(p_id))
        self.assertEqual(response1.status_code, 201)

        response2 = self.client.post(self.url_template.format(p_id))
        self.assertEqual(response2.status_code, 400)

        response_data = response2.json()
        self.assertIn('error', response_data)
        self.assertEqual(
            response_data['error'],
            "The product selected is already on user's favorites."
        )

    def test_add_favorite_invalid_product_id(self):
        """Test adding a product with invalid ID (doesn't exist in external API)"""
        p_id = 999999

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 400)
        response_data = response.json()

        self.assertIn('error', response_data)
        self.assertEqual(
            response_data['error'],
            "Product not found or could not be fetched from the API."
        )

        product_exists = Product.objects.filter(api_id=p_id).exists()
        self.assertFalse(product_exists)

    def test_add_favorite_without_authentication(self):
        """Test that endpoint requires authentication"""
        unauthenticated_client = Client()
        p_id = 4

        response = unauthenticated_client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 401)

    @patch('api.common.endpoints.ProductAPIClient')
    def test_add_favorite_api_request_exception(self, mock_client):
        """Test handling of API request failures"""
        p_id = 5

        mock_instance = Mock()
        mock_instance.get_product.side_effect = requests.RequestException("API Down")
        mock_client.return_value = mock_instance

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 400)
        response_data = response.json()

        self.assertIn('error', response_data)
        self.assertEqual(
            response_data['error'],
            "Product not found or could not be fetched from the API."
        )

    @patch('api.common.endpoints.ProductAPIClient')
    def test_add_favorite_api_key_error(self, mock_client):
        """Test handling of malformed API response (KeyError)"""
        p_id = 6

        mock_instance = Mock()
        mock_instance.get_product.return_value = {"incomplete": "data"}
        mock_client.return_value = mock_instance

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 400)
        response_data = response.json()

        self.assertIn('error', response_data)

    def test_add_favorite_multiple_products(self):
        """Test adding multiple different products to favorites"""
        product_ids = [7, 8, 9]

        for p_id in product_ids:
            response = self.client.post(self.url_template.format(p_id))
            self.assertEqual(response.status_code, 201)

        favorites_count = FavoriteProducts.objects.filter(user=self.user).count()
        self.assertEqual(favorites_count, len(product_ids))

    def test_add_favorite_returns_correct_product_data(self):
        """Test that the response contains correct product information"""
        p_id = 10

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 201)
        response_data = response.json()

        product = Product.objects.get(api_id=p_id)
        self.assertEqual(response_data['api_id'], product.api_id)
        self.assertEqual(response_data['title'], product.title)

        self.assertEqual(Decimal(str(response_data['price'])), product.price)

    def test_add_favorite_different_users_same_product(self):
        """Test that different users can favorite the same product"""
        p_id = 11

        response1 = self.client.post(self.url_template.format(p_id))
        self.assertEqual(response1.status_code, 201)

        user2, _ = TestHelper.create_customer_user(email="test1@email.com")
        client2 = TestHelper.client_from_user(user2)

        response2 = client2.post(self.url_template.format(p_id))
        self.assertEqual(response2.status_code, 201)

        favorites_count = FavoriteProducts.objects.filter(product__api_id=p_id).count()
        self.assertEqual(favorites_count, 2)

    def test_add_favorite_creates_product_once(self):
        """Test that product is only created once even with multiple users"""
        p_id = 12

        self.client.post(self.url_template.format(p_id))

        user2, _ = TestHelper.create_customer_user(email="test2@email.com")
        client2 = TestHelper.client_from_user(user2)
        client2.post(self.url_template.format(p_id))

        product_count = Product.objects.filter(api_id=p_id).count()
        self.assertEqual(product_count, 1)


class DeleteFavoriteTests(CommonTestCase):
    def setUp(self):
        super().setUp()
        self.url_template = "/api/common/favorites/{}/delete"

    def test_delete_favorite_success(self):
        """Test successfully deleting an existing favorite"""
        p_id = 1

        product = Product.objects.create(
            api_id=p_id,
            title="Test Product",
            price=Decimal("99.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )
        FavoriteProducts.objects.create(user=self.user, product=product)

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 204)

        favorite_exists = FavoriteProducts.objects.filter(
            user=self.user,
            product__api_id=p_id
        ).exists()
        self.assertFalse(favorite_exists)

    def test_delete_favorite_not_in_favorites(self):
        """Test deleting a product that is not in user's favorites"""
        p_id = 2

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "This product is not on your favorites.")

    def test_delete_favorite_nonexistent_product(self):
        """Test deleting a product that doesn't exist at all"""
        p_id = 999999

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "This product is not on your favorites.")

    def test_delete_favorite_without_authentication(self):
        """Test that endpoint requires authentication"""
        p_id = 3
        unauthenticated_client = Client()

        response = unauthenticated_client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 401)

    def test_delete_favorite_product_remains(self):
        """Test that deleting a favorite doesn't delete the product itself"""
        p_id = 4

        product = Product.objects.create(
            api_id=p_id,
            title="Test Product",
            price=Decimal("99.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )
        FavoriteProducts.objects.create(user=self.user, product=product)

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 204)

        product_exists = Product.objects.filter(api_id=p_id).exists()
        self.assertTrue(product_exists)

    def test_delete_favorite_only_users_favorite(self):
        """Test that deleting only removes the current user's favorite, not others'"""
        p_id = 5

        product = Product.objects.create(
            api_id=p_id,
            title="Test Product",
            price=Decimal("99.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )

        FavoriteProducts.objects.create(user=self.user, product=product)

        user2, _ = TestHelper.create_customer_user(email="test3@email.com")
        FavoriteProducts.objects.create(user=user2, product=product)

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 204)

        user1_favorite_exists = FavoriteProducts.objects.filter(
            user=self.user,
            product__api_id=p_id
        ).exists()
        self.assertFalse(user1_favorite_exists)

        user2_favorite_exists = FavoriteProducts.objects.filter(
            user=user2,
            product__api_id=p_id
        ).exists()
        self.assertTrue(user2_favorite_exists)

    def test_delete_favorite_multiple_times(self):
        """Test that deleting the same favorite twice returns error on second attempt"""
        p_id = 6

        product = Product.objects.create(
            api_id=p_id,
            title="Test Product",
            price=Decimal("99.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )
        FavoriteProducts.objects.create(user=self.user, product=product)

        response1 = self.client.post(self.url_template.format(p_id))
        self.assertEqual(response1.status_code, 204)

        response2 = self.client.post(self.url_template.format(p_id))
        self.assertEqual(response2.status_code, 400)
        self.assertEqual(response2.json(), "This product is not on your favorites.")

    def test_delete_favorite_different_product_id(self):
        """Test that deleting one favorite doesn't affect others"""
        p_id1 = 7
        p_id2 = 8

        product1 = Product.objects.create(
            api_id=p_id1,
            title="Test Product 1",
            price=Decimal("99.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )
        FavoriteProducts.objects.create(user=self.user, product=product1)

        product2 = Product.objects.create(
            api_id=p_id2,
            title="Test Product 2",
            price=Decimal("89.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )
        FavoriteProducts.objects.create(user=self.user, product=product2)

        response = self.client.post(self.url_template.format(p_id1))
        self.assertEqual(response.status_code, 204)

        favorite1_exists = FavoriteProducts.objects.filter(
            user=self.user,
            product__api_id=p_id1
        ).exists()
        self.assertFalse(favorite1_exists)

        favorite2_exists = FavoriteProducts.objects.filter(
            user=self.user,
            product__api_id=p_id2
        ).exists()
        self.assertTrue(favorite2_exists)

    def test_delete_favorite_returns_no_content(self):
        """Test that successful deletion returns 204 with no response body"""
        p_id = 9

        product = Product.objects.create(
            api_id=p_id,
            title="Test Product",
            price=Decimal("99.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )
        FavoriteProducts.objects.create(user=self.user, product=product)

        response = self.client.post(self.url_template.format(p_id))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')


class GetFavoritesTests(CommonTestCase):
    def setUp(self):
        super().setUp()
        self.url = "/api/common/favorites"

    def test_get_favorites_empty_list(self):
        """Test getting favorites when user has no favorites"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertIn('items', response_data)
        self.assertIn('count', response_data)
        self.assertEqual(response_data['items'], [])
        self.assertEqual(response_data['count'], 0)

    def test_get_favorites_single_product(self):
        """Test getting favorites with one product"""
        product = Product.objects.create(
            api_id=1,
            title="Test Product",
            price=Decimal("99.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )
        FavoriteProducts.objects.create(user=self.user, product=product)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['count'], 1)
        self.assertEqual(len(response_data['items']), 1)
        self.assertEqual(response_data['items'][0]['api_id'], 1)
        self.assertEqual(response_data['items'][0]['title'], "Test Product")

    def test_get_favorites_multiple_products(self):
        """Test getting favorites with multiple products"""
        for i in range(5):
            product = Product.objects.create(
                api_id=i + 1,
                title=f"Test Product {i + 1}",
                price=Decimal(f"{10 + i}.99"),
                description="Test description",
                category="test",
                image="https://example.com/image.png"
            )
            FavoriteProducts.objects.create(user=self.user, product=product)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['count'], 5)
        self.assertEqual(len(response_data['items']), 5)

    def test_get_favorites_ordered_by_date_created(self):
        """Test that favorites are ordered by date_created"""
        products = []
        for i in range(3):
            product = Product.objects.create(
                api_id=i + 1,
                title=f"Product {i + 1}",
                price=Decimal("99.99"),
                description="Test description",
                category="test",
                image="https://example.com/image.png"
            )
            FavoriteProducts.objects.create(user=self.user, product=product)
            products.append(product)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['items'][0]['api_id'], products[0].api_id)
        self.assertEqual(response_data['items'][1]['api_id'], products[1].api_id)
        self.assertEqual(response_data['items'][2]['api_id'], products[2].api_id)

    def test_get_favorites_pagination_first_page(self):
        """Test pagination on first page"""

        for i in range(25):
            product = Product.objects.create(
                api_id=i + 1,
                title=f"Product {i + 1}",
                price=Decimal("99.99"),
                description="Test description",
                category="test",
                image="https://example.com/image.png"
            )
            FavoriteProducts.objects.create(user=self.user, product=product)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['count'], 25)
        self.assertEqual(len(response_data['items']), 20)

    def test_get_favorites_pagination_second_page(self):
        """Test pagination on second page"""

        for i in range(25):
            product = Product.objects.create(
                api_id=i + 1,
                title=f"Product {i + 1}",
                price=Decimal("99.99"),
                description="Test description",
                category="test",
                image="https://example.com/image.png"
            )
            FavoriteProducts.objects.create(user=self.user, product=product)

        response = self.client.get(f"{self.url}?page=2")

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['count'], 25)
        self.assertEqual(len(response_data['items']), 5)

    def test_get_favorites_pagination_page_out_of_range(self):
        """Test requesting a page number that doesn't exist"""
        for i in range(5):
            product = Product.objects.create(
                api_id=i + 1,
                title=f"Product {i + 1}",
                price=Decimal("99.99"),
                description="Test description",
                category="test",
                image="https://example.com/image.png"
            )
            FavoriteProducts.objects.create(user=self.user, product=product)

        response = self.client.get(f"{self.url}?page=10")

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['items'], [])

    def test_get_favorites_without_authentication(self):
        """Test that endpoint requires authentication"""
        unauthenticated_client = Client()
        response = unauthenticated_client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_get_favorites_only_user_favorites(self):
        """Test that endpoint only returns current user's favorites"""
        product1 = Product.objects.create(
            api_id=1,
            title="Product 1",
            price=Decimal("99.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )
        product2 = Product.objects.create(
            api_id=2,
            title="Product 2",
            price=Decimal("89.99"),
            description="Test description",
            category="test",
            image="https://example.com/image.png"
        )

        FavoriteProducts.objects.create(user=self.user, product=product1)

        user2, _ = TestHelper.create_customer_user(email="test4@email.com")
        FavoriteProducts.objects.create(user=user2, product=product2)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['count'], 1)
        self.assertEqual(response_data['items'][0]['api_id'], 1)

    def test_get_favorites_returns_correct_schema(self):
        """Test that response matches ProductSchemaOut format"""
        product = Product.objects.create(
            api_id=1,
            title="Test Product",
            price=Decimal("99.99"),
            image="https://example.com/image.png",
            rating_rate=Decimal("4.5"),
            rating_count=100
        )
        FavoriteProducts.objects.create(user=self.user, product=product)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        item = response_data['items'][0]

        self.assertIn('api_id', item)
        self.assertIn('title', item)
        self.assertIn('price', item)
        self.assertIn('image', item)


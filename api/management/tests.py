# python
from decimal import Decimal

from django.test import TestCase, Client
import json

from api.models import AuthToken
from api.tests import TestHelper
from core.models import User, Product, FavoriteProducts


class ManagementTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user, _ = TestHelper.create_admin_user()
        self.client = TestHelper.client_from_user(self.user)


class GetUserListTests(ManagementTestCase):
    def setUp(self):
        super().setUp()
        self.url = "/api/management/user/list"

    def test_get_user_list_single_user(self):
        """Test getting user list with only admin user"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertIn('items', response_data)
        self.assertIn('count', response_data)
        self.assertGreaterEqual(response_data['count'], 1)

    def test_get_user_list_multiple_users(self):
        """Test getting user list with multiple users"""
        initial_response = self.client.get(self.url)
        initial_count = initial_response.json()['count']

        for i in range(5):
            TestHelper.create_customer_user(email=f"multiuser{i}@test.com")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['count'], initial_count + 5)

    def test_get_user_list_ordered_by_name(self):
        """Test that users are ordered by name"""
        TestHelper.create_customer_user(email="orderuser1@test.com", name="Zara")
        TestHelper.create_customer_user(email="orderuser2@test.com", name="Alice")
        TestHelper.create_customer_user(email="orderuser3@test.com", name="Mike")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        names = [item['name'] for item in response_data['items']]

        self.assertEqual(names, sorted(names))

    def test_get_user_list_pagination_first_page(self):
        """Test pagination on first page"""
        for i in range(25):
            TestHelper.create_customer_user(email=f"paginuser{i}@test.com")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertGreaterEqual(response_data['count'], 25)
        self.assertLessEqual(len(response_data['items']), 20)

    def test_get_user_list_pagination_second_page(self):
        """Test pagination on second page"""
        initial_response = self.client.get(self.url)
        initial_count = initial_response.json()['count']

        for i in range(25):
            TestHelper.create_customer_user(email=f"pagin2user{i}@test.com")

        response = self.client.get(f"{self.url}?page=2")

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        expected_count = initial_count + 25
        self.assertEqual(response_data['count'], expected_count)
        self.assertGreaterEqual(len(response_data['items']), 0)

    def test_get_user_list_pagination_page_out_of_range(self):
        """Test requesting a page number that doesn't exist"""
        response = self.client.get(f"{self.url}?page=999")

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['items'], [])

    def test_get_user_list_without_authentication(self):
        """Test that endpoint requires authentication"""
        unauthenticated_client = Client()
        response = unauthenticated_client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_get_user_list_non_admin_user(self):
        """Test that non-admin users cannot access the endpoint"""
        customer_user, _ = TestHelper.create_customer_user(email="nonadmin@test.com")
        customer_client = TestHelper.client_from_user(customer_user)

        response = customer_client.get(self.url)

        self.assertIn(response.status_code, [401, 403])

    def test_get_user_list_returns_correct_schema(self):
        """Test that response matches UserBaseSchema format"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertIn('items', response_data)
        self.assertIn('count', response_data)

        if len(response_data['items']) > 0:
            item = response_data['items'][0]

            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('email', item)


class CreateUserTests(ManagementTestCase):
    def setUp(self):
        super().setUp()
        self.url = "/api/management/user"

    def test_create_user_success(self):
        """Test successfully creating a new user"""
        payload = {
            "email": "newuser@test.com",
            "name": "New User",
            "password": "securepassword123"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        response_data = response.json()

        self.assertIn('id', response_data)
        self.assertIn('email', response_data)
        self.assertIn('name', response_data)
        self.assertEqual(response_data['email'], payload['email'])
        self.assertEqual(response_data['name'], payload['name'])

        user_exists = User.objects.filter(email=payload['email']).exists()
        self.assertTrue(user_exists)

    def test_create_user_token_created(self):
        """Test that an auth token is created for the new user"""
        payload = {
            "email": "tokenuser@test.com",
            "name": "Token User",
            "password": "password123"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email=payload['email'])
        token_exists = AuthToken.objects.filter(user=user).exists()
        self.assertTrue(token_exists)

    def test_create_user_duplicate_email(self):
        """Test that creating a user with duplicate email fails"""
        payload = {
            "email": "duplicate@test.com",
            "name": "First User",
            "password": "password123"
        }

        response1 = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 201)

        payload2 = {
            "email": "duplicate@test.com",
            "name": "Second User",
            "password": "differentpassword"
        }

        response2 = self.client.post(
            self.url,
            data=json.dumps(payload2),
            content_type='application/json'
        )

        self.assertEqual(response2.status_code, 400)
        self.assertIn('email', response2.json().lower() or 'use' in response2.json().lower())

    def test_create_user_missing_email(self):
        """Test that creating a user without email fails"""
        payload = {
            "name": "No Email User",
            "password": "password123"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 422)

    def test_create_user_missing_name(self):
        """Test that creating a user without name fails"""
        payload = {
            "email": "noname@test.com",
            "password": "password123"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 422)

    def test_create_user_missing_password(self):
        """Test that creating a user without password fails"""
        payload = {
            "email": "nopassword@test.com",
            "name": "No Password User"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 422)

    def test_create_user_without_authentication(self):
        """Test that endpoint requires authentication"""
        unauthenticated_client = Client()
        payload = {
            "email": "unauth@test.com",
            "name": "Unauth User",
            "password": "password123"
        }

        response = unauthenticated_client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_create_user_non_admin_user(self):
        """Test that non-admin users cannot create users"""
        customer_user, _ = TestHelper.create_customer_user(email="customer@test.com")
        customer_client = TestHelper.client_from_user(customer_user)

        payload = {
            "email": "newbycustomer@test.com",
            "name": "New User",
            "password": "password123"
        }

        response = customer_client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertIn(response.status_code, [401, 403])

    def test_create_user_password_is_hashed(self):
        """Test that password is properly hashed and not stored in plain text"""
        payload = {
            "email": "hashedpass@test.com",
            "name": "Hashed User",
            "password": "myplaintextpassword"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        user = User.objects.get(email=payload['email'])
        self.assertNotEqual(user.password, payload['password'])
        self.assertTrue(len(user.password) > 20)

    def test_create_user_returns_correct_schema(self):
        """Test that response matches UserSchemaOut format"""
        payload = {
            "email": "schematest@test.com",
            "name": "Schema User",
            "password": "password123"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        response_data = response.json()

        self.assertIn('id', response_data)
        self.assertIn('email', response_data)
        self.assertIn('name', response_data)

        self.assertNotIn('password', response_data)


class GetUserTests(ManagementTestCase):
    def setUp(self):
        super().setUp()
        self.url_template = "/api/management/user/{}"

    def test_get_user_success(self):
        """Test successfully retrieving a user by ID"""
        test_user, _ = TestHelper.create_customer_user(email="gettest@test.com")

        response = self.client.get(self.url_template.format(test_user.id))

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['id'], test_user.id)
        self.assertEqual(response_data['email'], test_user.email)
        self.assertEqual(response_data['name'], test_user.name)

    def test_get_user_not_found(self):
        """Test retrieving a non-existent user"""
        non_existent_id = 99999

        response = self.client.get(self.url_template.format(non_existent_id))

        self.assertEqual(response.status_code, 400)
        response_text = response.json().lower()
        self.assertTrue('user' in response_text or 'not found' in response_text)

    def test_get_user_returns_correct_schema(self):
        """Test that response matches UserBaseSchema format"""
        test_user, _ = TestHelper.create_customer_user(email="schema@test.com")

        response = self.client.get(self.url_template.format(test_user.id))

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertIn('id', response_data)
        self.assertIn('email', response_data)
        self.assertIn('name', response_data)

        self.assertNotIn('password', response_data)

    def test_get_user_without_authentication(self):
        """Test that endpoint requires authentication"""
        test_user, _ = TestHelper.create_customer_user(email="unauth@test.com")
        unauthenticated_client = Client()

        response = unauthenticated_client.get(self.url_template.format(test_user.id))

        self.assertEqual(response.status_code, 401)

    def test_get_user_non_admin_user(self):
        """Test that non-admin users cannot access the endpoint"""
        test_user, _ = TestHelper.create_customer_user(email="target@test.com")
        customer_user, _ = TestHelper.create_customer_user(email="requestor@test.com")
        customer_client = TestHelper.client_from_user(customer_user)

        response = customer_client.get(self.url_template.format(test_user.id))

        self.assertIn(response.status_code, [401, 403])

    def test_get_user_admin_user(self):
        """Test that admin users can retrieve their own data"""
        response = self.client.get(self.url_template.format(self.user.id))

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['id'], self.user.id)
        self.assertEqual(response_data['email'], self.user.email)


import json


class UpdateUserTests(ManagementTestCase):
    def setUp(self):
        super().setUp()
        self.url_template = "/api/management/user/{}"

    def test_update_user_name_success(self):
        """Test successfully updating a user's name"""
        test_user, _ = TestHelper.create_customer_user(email="updatename@test.com", name="Old Name")

        payload = {"name": "New Name"}

        response = self.client.put(
            self.url_template.format(test_user.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['name'], "New Name")

        test_user.refresh_from_db()
        self.assertEqual(test_user.name, "New Name")

    def test_update_user_email_success(self):
        """Test successfully updating a user's email"""
        test_user, _ = TestHelper.create_customer_user(email="oldemail@test.com")

        payload = {"email": "newemail@test.com"}

        response = self.client.put(
            self.url_template.format(test_user.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['email'], "newemail@test.com")

        test_user.refresh_from_db()
        self.assertEqual(test_user.email, "newemail@test.com")

    def test_update_user_password_success(self):
        """Test successfully updating a user's password"""
        test_user, _ = TestHelper.create_customer_user(email="updatepass@test.com")
        old_password = test_user.password

        payload = {"password": "newpassword123"}

        response = self.client.put(
            self.url_template.format(test_user.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        test_user.refresh_from_db()
        self.assertNotEqual(test_user.password, old_password)
        self.assertNotEqual(test_user.password, "newpassword123")

    def test_update_user_multiple_fields(self):
        """Test updating multiple fields at once"""
        test_user, _ = TestHelper.create_customer_user(email="multi@test.com", name="Old Name")

        payload = {
            "name": "Updated Name",
            "email": "updated@test.com"
        }

        response = self.client.put(
            self.url_template.format(test_user.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        test_user.refresh_from_db()
        self.assertEqual(test_user.name, "Updated Name")
        self.assertEqual(test_user.email, "updated@test.com")

    def test_update_user_not_found(self):
        """Test updating a non-existent user"""
        non_existent_id = 99999
        payload = {"name": "New Name"}

        response = self.client.put(
            self.url_template.format(non_existent_id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        response_text = response.json().lower()
        self.assertTrue('user' in response_text or 'not found' in response_text)

    def test_update_user_duplicate_email(self):
        """Test updating to an email that already exists"""
        user1, _ = TestHelper.create_customer_user(email="existing@test.com")
        user2, _ = TestHelper.create_customer_user(email="toupdate@test.com")

        payload = {"email": "existing@test.com"}

        response = self.client.put(
            self.url_template.format(user2.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        response_text = response.json().lower()
        self.assertTrue('email' in response_text or 'use' in response_text)

    def test_update_user_partial_update(self):
        """Test that only provided fields are updated"""
        test_user, _ = TestHelper.create_customer_user(email="partial@test.com", name="Original Name")

        payload = {"name": "Updated Name"}

        response = self.client.put(
            self.url_template.format(test_user.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        test_user.refresh_from_db()
        self.assertEqual(test_user.name, "Updated Name")
        self.assertEqual(test_user.email, "partial@test.com")

    def test_update_user_without_authentication(self):
        """Test that endpoint requires authentication"""
        test_user, _ = TestHelper.create_customer_user(email="noauth@test.com")
        unauthenticated_client = Client()

        payload = {"name": "New Name"}

        response = unauthenticated_client.put(
            self.url_template.format(test_user.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_update_user_non_admin_user(self):
        """Test that non-admin users cannot update users"""
        target_user, _ = TestHelper.create_customer_user(email="target@test.com")
        customer_user, _ = TestHelper.create_customer_user(email="requestor@test.com")
        customer_client = TestHelper.client_from_user(customer_user)

        payload = {"name": "Hacked Name"}

        response = customer_client.put(
            self.url_template.format(target_user.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertIn(response.status_code, [401, 403])

    def test_update_user_returns_correct_schema(self):
        """Test that response matches UserSchemaOut format"""
        test_user, _ = TestHelper.create_customer_user(email="schema@test.com")

        payload = {"name": "Schema Name"}

        response = self.client.put(
            self.url_template.format(test_user.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertIn('id', response_data)
        self.assertIn('email', response_data)
        self.assertIn('name', response_data)

        self.assertNotIn('password', response_data)

    def test_update_user_empty_payload(self):
        """Test updating with no fields should still work"""
        test_user, _ = TestHelper.create_customer_user(email="empty@test.com", name="Original")

        payload = {}

        response = self.client.put(
            self.url_template.format(test_user.id),
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        test_user.refresh_from_db()
        self.assertEqual(test_user.name, "Original")


class DeleteUserTests(ManagementTestCase):
    def setUp(self):
        super().setUp()
        self.url_template = "/api/management/user/{}"

    def test_delete_user_success(self):
        """Test successfully deleting a user"""
        test_user, _ = TestHelper.create_customer_user(email="deleteme@test.com")
        user_id = test_user.id

        response = self.client.delete(self.url_template.format(user_id))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')

        user_exists = User.objects.filter(id=user_id).exists()
        self.assertFalse(user_exists)

    def test_delete_user_not_found(self):
        """Test deleting a non-existent user"""
        non_existent_id = 99999

        response = self.client.delete(self.url_template.format(non_existent_id))

        self.assertEqual(response.status_code, 400)
        response_text = response.json().lower()
        self.assertTrue('user' in response_text or 'not found' in response_text)

    def test_delete_user_cascades_to_auth_token(self):
        """Test that deleting a user also deletes their auth token"""
        test_user, token = TestHelper.create_customer_user(email="withtoken@test.com")
        user_id = test_user.id

        self.assertTrue(AuthToken.objects.filter(user=test_user).exists())

        response = self.client.delete(self.url_template.format(user_id))

        self.assertEqual(response.status_code, 204)

        token_exists = AuthToken.objects.filter(user_id=user_id).exists()
        self.assertFalse(token_exists)

    def test_delete_user_cascades_to_favorites(self):
        """Test that deleting a user also deletes their favorites"""
        test_user, _ = TestHelper.create_customer_user(email="withfavorites@test.com")

        product = Product.objects.create(
            api_id=1,
            title="Test Product",
            price=Decimal("99.99"),
            description="Test",
            category="test",
            image="https://example.com/image.png"
        )
        FavoriteProducts.objects.create(user=test_user, product=product)

        user_id = test_user.id

        self.assertTrue(FavoriteProducts.objects.filter(user=test_user).exists())

        response = self.client.delete(self.url_template.format(user_id))

        self.assertEqual(response.status_code, 204)

        favorite_exists = FavoriteProducts.objects.filter(user_id=user_id).exists()
        self.assertFalse(favorite_exists)

    def test_delete_user_multiple_times(self):
        """Test that deleting the same user twice returns error on second attempt"""
        test_user, _ = TestHelper.create_customer_user(email="deletedouble@test.com")
        user_id = test_user.id

        response1 = self.client.delete(self.url_template.format(user_id))
        self.assertEqual(response1.status_code, 204)

        response2 = self.client.delete(self.url_template.format(user_id))
        self.assertEqual(response2.status_code, 400)

    def test_delete_user_without_authentication(self):
        """Test that endpoint requires authentication"""
        test_user, _ = TestHelper.create_customer_user(email="noauth@test.com")
        unauthenticated_client = Client()

        response = unauthenticated_client.delete(self.url_template.format(test_user.id))

        self.assertEqual(response.status_code, 401)

    def test_delete_user_non_admin_user(self):
        """Test that non-admin users cannot delete users"""
        target_user, _ = TestHelper.create_customer_user(email="target@test.com")
        customer_user, _ = TestHelper.create_customer_user(email="requestor@test.com")
        customer_client = TestHelper.client_from_user(customer_user)

        response = customer_client.delete(self.url_template.format(target_user.id))

        self.assertIn(response.status_code, [401, 403])

    def test_delete_user_returns_no_content(self):
        """Test that successful deletion returns 204 with no response body"""
        test_user, _ = TestHelper.create_customer_user(email="nocontent@test.com")

        response = self.client.delete(self.url_template.format(test_user.id))

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b'')

    def test_delete_user_does_not_delete_product(self):
        """Test that deleting a user doesn't delete products they favorited"""
        test_user, _ = TestHelper.create_customer_user(email="keepproduct@test.com")

        product = Product.objects.create(
            api_id=1,
            title="Test Product",
            price=Decimal("99.99"),
            description="Test",
            category="test",
            image="https://example.com/image.png"
        )
        FavoriteProducts.objects.create(user=test_user, product=product)

        response = self.client.delete(self.url_template.format(test_user.id))

        self.assertEqual(response.status_code, 204)

        product_exists = Product.objects.filter(id=product.id).exists()
        self.assertTrue(product_exists)

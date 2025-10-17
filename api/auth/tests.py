from django.test import TestCase, Client

from api.models import AuthToken
from api.tests import TestHelper

class AuthTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.user, _ = TestHelper.create_customer_user()
        self.client = TestHelper.client_from_user(self.user)


class GetAuthUserTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.url = "/api/auth/user"
        
    def test_get_auth_user_success(self):
        """Test successfully retrieving authenticated user information"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], self.user.email)
        self.assertEqual(response.json()['name'], self.user.name)

    def test_get_auth_user_without_token(self):
        """Test that endpoint returns 401 when no authentication token is provided"""
        unauthenticated_client = Client()
        response = unauthenticated_client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_get_auth_user_with_invalid_token(self):
        """Test that endpoint returns 401 when invalid token is provided"""
        client = Client(headers={"X-API-Key": "thisisafaketoken!"})
        response = client.get(
            self.url,
        )

        self.assertEqual(response.status_code, 401)

    def test_get_auth_user_returns_correct_schema(self):
        """Test that the response matches the expected UserSchemaOut format"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertIn('email', response_data)
        self.assertIn('name', response_data)

    def test_get_auth_user_with_deleted_token(self):
        """Test that endpoint returns 401 when user's token has been deleted"""
        AuthToken.objects.filter(user=self.user).delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)


class GetAuthTokenTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.url = "/api/auth/token"
        
    def test_get_auth_token_success(self):
        """Test successfully retrieving authenticated user's token"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 201)

        token = response.json()
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)

        self.assertEqual(token, self.user.token)

    def test_get_auth_token_without_authentication(self):
        """Test that endpoint returns 401 when no authentication is provided"""
        unauthenticated_client = Client()
        response = unauthenticated_client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_get_auth_token_with_invalid_token(self):
        """Test that endpoint returns 401 when invalid token is provided"""
        client = Client(headers={"X-API-Key": "thisisafaketoken!"})
        response = client.get(
            self.url,
        )

        self.assertEqual(response.status_code, 401)

    def test_get_auth_token_returns_string(self):
        """Test that the response is a valid string token"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 201)
        token = response.json()

        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    def test_get_auth_token_with_deleted_token(self):
        """Test that endpoint returns 401 when user's token has been deleted"""
        AuthToken.objects.filter(user=self.user).delete()

        unauthenticated_client = Client()
        response = unauthenticated_client.get(self.url)

        self.assertEqual(response.status_code, 401)

    def test_get_auth_token_multiple_calls_same_token(self):
        """Test that multiple calls return the same token"""
        response1 = self.client.get(self.url)
        response2 = self.client.get(self.url)

        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response2.status_code, 201)

        token1 = response1.json()
        token2 = response2.json()

        self.assertEqual(token1, token2)


import json
from django.test import TestCase, Client

class LoginTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        self.url = "/api/auth/login"
        self.password = "abc"

    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = self.client.post(
            self.url,
            data=json.dumps({"email": self.user.email, "password": self.password}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertIn('token', response_data)
        self.assertIsInstance(response_data['token'], str)
        self.assertTrue(len(response_data['token']) > 0)

    def test_login_returns_existing_token(self):
        """Test that login returns the existing token for a user"""
        existing_token = AuthToken.objects.get(user=self.user)

        response = self.client.post(
            self.url,
            data=json.dumps({"email": self.user.email, "password": self.password}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertEqual(response_data['token'], existing_token.key)

    def test_login_with_invalid_password(self):
        """Test login fails with incorrect password"""
        response = self.client.post(
            self.url,
            data=json.dumps({"email": self.user.email, "password": "wrongpassword"}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        response_data = response.json()

        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], "Invalid email or password.")

    def test_login_with_nonexistent_email(self):
        """Test login fails with non-existent email"""
        response = self.client.post(
            self.url,
            data=json.dumps({"email": "nonexistent@example.com", "password": self.password}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        response_data = response.json()

        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], "Invalid email or password.")

    def test_login_with_empty_email(self):
        """Test login fails with empty email"""
        response = self.client.post(
            self.url,
            data=json.dumps({"email": "", "password": self.password}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_login_with_empty_password(self):
        """Test login fails with empty password"""
        response = self.client.post(
            self.url,
            data=json.dumps({"email": self.user.email, "password": ""}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_login_creates_token_if_not_exists(self):
        """Test that login creates a token if user doesn't have one"""
        AuthToken.objects.filter(user=self.user).delete()

        response = self.client.post(
            self.url,
            data=json.dumps({"email": self.user.email, "password": self.password}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        self.assertIn('token', response_data)
        token_exists = AuthToken.objects.filter(user=self.user).exists()
        self.assertTrue(token_exists)

    def test_login_case_sensitive_email(self):
        """Test that email matching is case-sensitive"""
        response = self.client.post(
            self.url,
            data=json.dumps({"email": self.user.email.upper(), "password": self.password}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

    def test_login_multiple_times_same_token(self):
        """Test that logging in multiple times returns the same token"""
        response1 = self.client.post(
            self.url,
            data=json.dumps({"email": self.user.email, "password": self.password}),
            content_type='application/json'
        )
        response2 = self.client.post(
            self.url,
            data=json.dumps({"email": self.user.email, "password": self.password}),
            content_type='application/json'
        )

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        token1 = response1.json()['token']
        token2 = response2.json()['token']

        self.assertEqual(token1, token2)

    def test_login_without_authentication_header(self):
        """Test that login endpoint doesn't require authentication (auth=None)"""
        unauthenticated_client = Client()
        response = unauthenticated_client.post(
            self.url,
            data=json.dumps({"email": self.user.email, "password": self.password}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

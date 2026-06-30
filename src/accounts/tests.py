from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='abdo',
            password='Test@1234'
        )

        self.login_url = '/api/auth/login/'
        self.protected_url = '/api/protected/'  
        self.logout_url = '/api/auth/logout/'
        self.ChangePassword_url = '/api/auth/change-password/'

    # =========================
    # Successful Login
    # =========================
    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {
                'username': 'abdo',
                'password': 'Test@1234'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        self.assertIsInstance(response.data['access'], str)
        self.assertGreater(len(response.data['access']), 20)

    # =========================
    # Wrong Password
    # =========================
    def test_login_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {
                'username': 'abdo',
                'password': 'wrongpass'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 401)

    # =========================
    # User Not Found
    # =========================
    def test_login_user_not_found(self):
        response = self.client.post(
            self.login_url,
            {
                'username': 'not_exist',
                'password': '123456'
            },
            format='json'
        )   

        self.assertEqual(response.status_code, 401)

    # =========================
    # Missing Fields
    # =========================
    def test_login_missing_fields(self):
        response = self.client.post(
            self.login_url,
            {
                'username': 'abdo'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 400)

    # =========================
    # Empty Password
    # =========================
    def test_login_empty_password(self):
        response = self.client.post(
            self.login_url,
            {
                'username': 'abdo',
                'password': ''
            },
            format='json'
        )

        self.assertEqual(response.status_code, 400)

    # =========================
    # Access Protected WITH Token
    # =========================
    def test_access_protected_with_token(self):
        login_response = self.client.post(
            self.login_url,
            {
                'username': 'abdo',
                'password': 'Test@1234'
            },
            format='json'
        )

        token = login_response.data['access']

        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + token
        )

        response = self.client.get(self.protected_url)

        self.assertEqual(response.status_code, 200)

    # =========================
    # Access Protected WITHOUT Token
    # =========================
    def test_access_protected_without_token(self):
        response = self.client.get(self.protected_url)

        self.assertEqual(response.status_code, 401)

    # =========================
    # Security Test (SQL Injection)
    # =========================
    def test_login_sql_injection(self):
        response = self.client.post(
            self.login_url,
            {
                'username': "abdo' OR 1=1 --",
                'password': 'anything'
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, 401)

    # =========================
    # Logout Test               
    # =========================
    def test_logout(self):
    
        login_response = self.client.post(
            self.login_url,
            {
                'username': 'abdo',
                'password': 'Test@1234'
            },
            format='json'
        )
    
        self.assertEqual(login_response.status_code, 200)
    
        access_token = login_response.data['access']
        refresh_token = login_response.data.get('refresh')
    
        self.assertIsNotNone(refresh_token)
    
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + access_token
        )
    
        response = self.client.post(
            self.logout_url,
            {
                'refresh': refresh_token
            },
            format='json'
        )
    
    
        self.assertEqual(response.status_code, 205)
        
    # =========================
    # Change Password Test 
    # =========================
    def test_change_password(self):
        login_response = self.client.post(
            self.login_url,
            {
                'username': 'abdo',
                'password': 'Test@1234'
            },
            format='json'
        )
        
        self.assertEqual(login_response.status_code, 200)
        
        access_token = login_response.data['access']
        refresh_token = login_response.data.get('refresh')
        self.assertIsNotNone(refresh_token)
        
        self.client.credentials(
            HTTP_AUTHORIZATION='Bearer ' + access_token
        )
        
        response = self.client.post(
            self.ChangePassword_url,
            {
                'old_password': 'Test@1234',
                'new_password': 'NewPass@1234',
                'confirm_password': 'NewPass@1234'
            },
            format='json'
        )  
        
        print(response.data)
        
        self.assertEqual(response.status_code, 200)
        
        self.client = APIClient()
        
        login_response = self.client.post(
            self.login_url,
            {
                'username': 'abdo',
                'password': 'NewPass@1234'
            },
            format='json'
        )
        
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)
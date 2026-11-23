from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import UserProfile


class AccountsRoleAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_customer_registration(self):
        """Test customer registration creates user and customer profile."""
        response = self.client.post(reverse('customer_register'), {
            'username': 'newplayer',
            'full_name': 'New Player',
            'email': 'newplayer@example.com',
            'phone': '9876543210',
            'password': 'strongpassword123',
            'confirm_password': 'strongpassword123'
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newplayer')
        self.assertEqual(user.profile.role, 'CUSTOMER')

    def test_owner_registration(self):
        """Test turf owner registration creates user and owner profile."""
        response = self.client.post(reverse('owner_register'), {
            'username': 'newowner',
            'business_name': 'Elite Sports Arena',
            'full_name': 'Elite Owner',
            'email': 'elite@example.com',
            'phone': '9876543211',
            'upi_id': 'elite@upi',
            'password': 'strongpassword123',
            'confirm_password': 'strongpassword123'
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newowner')
        self.assertEqual(user.profile.role, 'OWNER')
        self.assertEqual(user.profile.upi_id, 'elite@upi')

    def test_role_based_access_control(self):
        """Customer cannot access owner dashboard; redirected with notice."""
        cust = User.objects.create_user(username='custuser', password='password123')
        cust.profile.role = 'CUSTOMER'
        cust.profile.save()

        self.client.login(username='custuser', password='password123')
        response = self.client.get(reverse('owner_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('customer_dashboard'))

from datetime import time
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from turfs.models import Turf, Review
from accounts.models import UserProfile


class TurfManagementTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='turf_boss', password='password123')
        self.owner.profile.role = 'OWNER'
        self.owner.profile.save()

        self.customer = User.objects.create_user(username='regular_player', password='password123')
        self.customer.profile.role = 'CUSTOMER'
        self.customer.profile.save()

        self.client = Client()

    def test_owner_add_turf(self):
        self.client.login(username='turf_boss', password='password123')
        response = self.client.post(reverse('add_turf'), {
            'name': 'Sambhajinagar Box Arena',
            'city': 'Chhatrapati Sambhajinagar',
            'area': 'Jalna Road',
            'address': 'Near Seven Hills, Jalna Road',
            'turf_type': 'Box Cricket',
            'size': '100 x 60 ft',
            'available_sports': 'Box Cricket, Cricket',
            'hourly_price': '850.00',
            'opening_time': '06:00',
            'closing_time': '23:00',
            'slot_duration_minutes': '60',
            'facilities': 'Floodlights, Parking, Washroom',
            'contact_number': '+91 98765 00000',
            'description': 'Excellent night box cricket turf.',
            'rules_and_regulations': 'Non-marking shoes only.',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Turf.objects.filter(name='Sambhajinagar Box Arena').exists())

    def test_customer_cannot_add_turf(self):
        self.client.login(username='regular_player', password='password123')
        response = self.client.get(reverse('add_turf'))
        self.assertEqual(response.status_code, 302)
        # Redirected away from owner page
        self.assertRedirects(response, reverse('customer_dashboard'))

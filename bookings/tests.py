from datetime import datetime, date, time, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from accounts.models import UserProfile
from turfs.models import Turf, BlockedSlot
from bookings.models import Booking, Payment
from turfs.slot_utils import generate_turf_slots


class TurfBookingAndConcurrencyTests(TestCase):
    def setUp(self):
        # 1. Create Owner & Customer
        self.owner = User.objects.create_user(username='test_owner', password='password123')
        self.owner_profile = UserProfile.objects.get_or_create(user=self.owner, defaults={'role': 'OWNER', 'upi_id': 'owner@upi'})[0]
        self.owner_profile.role = 'OWNER'
        self.owner_profile.save()

        self.customer1 = User.objects.create_user(username='player1', password='password123')
        self.customer1_profile = UserProfile.objects.get_or_create(user=self.customer1, defaults={'role': 'CUSTOMER'})[0]

        self.customer2 = User.objects.create_user(username='player2', password='password123')
        self.customer2_profile = UserProfile.objects.get_or_create(user=self.customer2, defaults={'role': 'CUSTOMER'})[0]

        # 2. Create Turf
        self.turf = Turf.objects.create(
            owner=self.owner,
            name='Test Football Arena',
            slug='test-football-arena',
            city='Chhatrapati Sambhajinagar',
            area='CIDCO',
            address='Near Cannaught',
            turf_type='Football',
            hourly_price=800.00,
            opening_time=time(6, 0),
            closing_time=time(22, 0),
            slot_duration_minutes=60,
            available_sports='Football'
        )

        self.client = Client()

    def test_dynamic_slot_generation(self):
        """Tests that slots are generated according to opening and closing hours."""
        target_date = timezone.localdate() + timedelta(days=2)
        slots = generate_turf_slots(self.turf, target_date)
        
        # 06:00 to 22:00 = 16 hourly slots
        self.assertEqual(len(slots), 16)
        self.assertTrue(slots[0]['is_available'])
        self.assertEqual(slots[0]['start_time'], '06:00')

    def test_double_booking_prevention(self):
        """Tests that an already booked slot cannot be double booked."""
        target_date = timezone.localdate() + timedelta(days=3)
        slot_time = time(17, 0)

        # 1. Player 1 books the slot
        self.client.login(username='player1', password='password123')
        response1 = self.client.post(reverse('initiate_booking', kwargs={'slug': self.turf.slug}), {
            'booking_date': target_date.strftime('%Y-%m-%d'),
            'start_time': slot_time.strftime('%H:%M:%S'),
            'end_time': time(18, 0).strftime('%H:%M:%S'),
            'sport': 'Football',
            'player_name': 'Player One',
            'player_phone': '9876543210'
        })
        self.assertEqual(response1.status_code, 302) # Redirect to checkout

        # Verify booking created in DB
        self.assertTrue(Booking.objects.filter(turf=self.turf, booking_date=target_date, start_time=slot_time).exists())

        # 2. Player 2 attempts to book the SAME slot
        self.client.login(username='player2', password='password123')
        response2 = self.client.post(reverse('initiate_booking', kwargs={'slug': self.turf.slug}), {
            'booking_date': target_date.strftime('%Y-%m-%d'),
            'start_time': slot_time.strftime('%H:%M:%S'),
            'end_time': time(18, 0).strftime('%H:%M:%S'),
            'sport': 'Football',
            'player_name': 'Player Two',
            'player_phone': '9876543211'
        })
        
        # Must redirect back to detail page with error message (not creating a 2nd booking)
        self.assertEqual(Booking.objects.filter(turf=self.turf, booking_date=target_date, start_time=slot_time).count(), 1)

    def test_cancellation_policy_outside_30_minutes(self):
        """Customer can cancel if match is > 30 minutes away."""
        future_date = timezone.localdate() + timedelta(days=5)
        booking = Booking.objects.create(
            turf=self.turf,
            customer=self.customer1,
            sport='Football',
            booking_date=future_date,
            start_time=time(19, 0),
            end_time=time(20, 0),
            total_price=800.00,
            player_name='Player One',
            player_phone='9876543210',
            status='CONFIRMED'
        )
        
        can_cancel, _ = booking.can_cancel()
        self.assertTrue(can_cancel)

        # Cancel via view
        self.client.login(username='player1', password='password123')
        response = self.client.post(reverse('cancel_booking', kwargs={'booking_id': booking.booking_id}), {
            'cancellation_reason': 'Weather issue'
        })
        self.assertEqual(response.status_code, 302)
        
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CANCELLED')
        self.assertIsNotNone(booking.cancelled_at)

    def test_cancellation_policy_locked_inside_30_minutes(self):
        """Customer CANNOT cancel if match starts in less than 30 minutes."""
        now = timezone.localtime(timezone.now())
        # Set booking to start 10 minutes from now
        match_start_dt = now + timedelta(minutes=10)
        
        booking = Booking.objects.create(
            turf=self.turf,
            customer=self.customer1,
            sport='Football',
            booking_date=match_start_dt.date(),
            start_time=match_start_dt.time(),
            end_time=(match_start_dt + timedelta(hours=1)).time(),
            total_price=800.00,
            player_name='Player One',
            player_phone='9876543210',
            status='CONFIRMED'
        )

        can_cancel, reason = booking.can_cancel()
        self.assertFalse(can_cancel)
        self.assertIn("30 minutes", reason)

        # Attempt to cancel via view should be rejected
        self.client.login(username='player1', password='password123')
        response = self.client.post(reverse('cancel_booking', kwargs={'booking_id': booking.booking_id}), {})
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'CONFIRMED') # Remains confirmed!

    def test_upi_qr_payment_workflow_and_owner_verification(self):
        """Tests the payment submission and admin verification flow."""
        future_date = timezone.localdate() + timedelta(days=2)
        booking = Booking.objects.create(
            turf=self.turf,
            customer=self.customer1,
            sport='Football',
            booking_date=future_date,
            start_time=time(16, 0),
            end_time=time(17, 0),
            total_price=800.00,
            player_name='Player One',
            player_phone='9876543210',
            status='PENDING'
        )
        payment = Payment.objects.create(
            booking=booking,
            amount=800.00,
            status='PENDING'
        )

        # Customer submits UTR
        self.client.login(username='player1', password='password123')
        res = self.client.post(reverse('checkout_payment', kwargs={'booking_id': booking.booking_id}), {
            'upi_reference_id': '432198007612'
        })
        self.assertEqual(res.status_code, 302)
        payment.refresh_from_db()
        self.assertEqual(payment.upi_reference_id, '432198007612')
        self.assertEqual(payment.status, 'PENDING')

        # Owner verifies payment
        self.client.login(username='test_owner', password='password123')
        verify_res = self.client.post(reverse('verify_payment_action', kwargs={'payment_id': payment.id}), {
            'action': 'approve'
        })
        self.assertEqual(verify_res.status_code, 302)
        
        payment.refresh_from_db()
        booking.refresh_from_db()
        self.assertEqual(payment.status, 'PAID')
        self.assertEqual(booking.status, 'CONFIRMED')

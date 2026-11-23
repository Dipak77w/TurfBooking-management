import uuid
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from turfs.models import Turf


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('REJECTED', 'Payment Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    booking_id = models.CharField(max_length=30, unique=True, editable=False)
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    sport = models.CharField(max_length=100)
    
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    
    player_name = models.CharField(max_length=150)
    player_phone = models.CharField(max_length=20)
    player_email = models.EmailField(blank=True)
    special_notes = models.TextField(blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    cancellation_reason = models.TextField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date', '-start_time']
        indexes = [
            models.Index(fields=['turf', 'booking_date', 'start_time']),
            models.Index(fields=['customer', 'status']),
        ]

    def __str__(self):
        return f"{self.booking_id} - {self.turf.name} ({self.booking_date} {self.start_time.strftime('%H:%M')})"

    def save(self, *args, **kwargs):
        if not self.booking_id:
            date_prefix = timezone.now().strftime('%Y%m%d')
            rand_code = uuid.uuid4().hex[:6].upper()
            self.booking_id = f"TRF-{date_prefix}-{rand_code}"
        super().save(*args, **kwargs)

    @property
    def start_datetime(self):
        """Returns timezone-aware datetime for the booking start."""
        tz = timezone.get_current_timezone()
        naive_dt = datetime.combine(self.booking_date, self.start_time)
        return timezone.make_aware(naive_dt, tz)

    @property
    def end_datetime(self):
        """Returns timezone-aware datetime for the booking end."""
        tz = timezone.get_current_timezone()
        naive_dt = datetime.combine(self.booking_date, self.end_time)
        return timezone.make_aware(naive_dt, tz)

    def can_cancel(self):
        """
        Cancellation Policy:
        - Customer can cancel ONLY before 30 minutes of the scheduled starting time.
        - If less than 30 minutes remain, disable cancellation.
        - Cannot cancel already cancelled, rejected, or completed bookings.
        """
        if self.status in ['CANCELLED', 'REJECTED']:
            return False, "This booking is already cancelled or rejected."
        
        if self.status == 'COMPLETED':
            return False, "Completed bookings cannot be cancelled."

        now = timezone.now()
        start_dt = self.start_datetime

        if now >= start_dt:
            return False, "This match slot has already started or elapsed."

        time_difference = start_dt - now
        if time_difference < timedelta(minutes=30):
            remaining_mins = int(time_difference.total_seconds() // 60)
            return False, f"Cancellation locked: Bookings can only be cancelled up to 30 minutes before match start time. (Only {remaining_mins} minutes remaining)."

        return True, "Eligible for cancellation."

    @property
    def is_past(self):
        return timezone.now() >= self.end_datetime

    @property
    def is_cancellable(self):
        eligible, _ = self.can_cancel()
        return eligible

    @property
    def slot_display(self):
        return f"{self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending Verification'),
        ('PAID', 'Verified & Confirmed'),
        ('REJECTED', 'Rejected / Invalid UTR'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    upi_reference_id = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="12-digit UPI UTR / Transaction Reference ID from Google Pay, PhonePe, Paytm, etc."
    )
    payment_screenshot = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    payment_method = models.CharField(max_length=50, default='UPI QR Scanner')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for {self.booking.booking_id} - ₹{self.amount} ({self.get_status_display()})"

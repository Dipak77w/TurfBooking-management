from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('CUSTOMER', 'Player / Customer'),
        ('OWNER', 'Turf Owner (Admin)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='CUSTOMER')
    phone = models.CharField(max_length=15, blank=True)
    city = models.CharField(max_length=100, default='Chhatrapati Sambhajinagar')
    address = models.TextField(blank=True)
    
    # Turf Owner specific fields
    business_name = models.CharField(max_length=150, blank=True, null=True, help_text="e.g. Sambhajinagar Sports Club")
    upi_id = models.CharField(max_length=100, blank=True, null=True, help_text="Owner's UPI ID for customer payments, e.g. owner@upi")
    upi_qr_image = models.ImageField(upload_to='upi_qr/', blank=True, null=True, help_text="Upload custom UPI QR Code scanner image")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_owner(self):
        return self.role == 'OWNER'

    @property
    def is_customer(self):
        return self.role == 'CUSTOMER'

    @property
    def full_name(self):
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full if full else self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        default_role = 'OWNER' if instance.is_superuser else 'CUSTOMER'
        UserProfile.objects.get_or_create(user=instance, defaults={'role': default_role})

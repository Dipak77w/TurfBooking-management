from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import Avg


class Turf(models.Model):
    TURF_TYPE_CHOICES = [
        ('Football', 'Football Turf (Natural / Artificial Grass)'),
        ('Box Cricket', 'Box Cricket Turf (Synthetic Grass)'),
        ('Cricket & Football', 'Cricket & Football Multi-Turf'),
        ('Multi-Sport Arena', 'Multi-Sport Arena (Cricket, Football, Volleyball)'),
        ('Badminton', 'Indoor Badminton Court (Wooden / Synthetic)'),
        ('Tennis', 'Lawn Tennis Court'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turfs')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    city = models.CharField(max_length=100, default='Chhatrapati Sambhajinagar')
    area = models.CharField(max_length=150, help_text="e.g. CIDCO Cannaught Place, Beed Bypass, Seven Hills")
    address = models.TextField(help_text="Full address with landmark")
    google_maps_url = models.CharField(max_length=600, blank=True, help_text="Google Maps share link or iframe embed URL")
    
    turf_type = models.CharField(max_length=60, choices=TURF_TYPE_CHOICES, default='Box Cricket')
    size = models.CharField(max_length=100, default='110 x 65 ft', help_text="e.g., 110 x 65 ft, 7-A-Side Football, Standard Box Cricket")
    available_sports = models.CharField(max_length=250, default='Box Cricket, Football', help_text="Comma-separated: Box Cricket, Football, Volleyball")
    
    description = models.TextField()
    hourly_price = models.DecimalField(max_digits=8, decimal_places=2, default=800.00, help_text="Price per hour in INR (₹)")
    
    opening_time = models.TimeField(default='06:00:00', help_text="Turf opening hour")
    closing_time = models.TimeField(default='23:00:00', help_text="Turf closing hour")
    slot_duration_minutes = models.PositiveIntegerField(default=60, help_text="Slot duration in minutes (standard: 60)")
    
    facilities = models.CharField(
        max_length=350, 
        default='Floodlights, Parking, Drinking Water, Washroom, Changing Room',
        help_text="Comma-separated: Floodlights, Parking, Drinking Water, Washroom, Changing Room, Cafeteria, First Aid"
    )
    
    contact_number = models.CharField(max_length=20, default='+91 98765 43210')
    rules_and_regulations = models.TextField(
        blank=True,
        default="1. Non-marking sports shoes or turf studs only (metal studs strictly prohibited).\n"
                "2. Please report 10 minutes prior to your booked slot.\n"
                "3. Smoking and consumption of alcohol are strictly banned inside the arena.\n"
                "4. Management is not responsible for loss of personal belongings.\n"
                "5. Any physical damage to turf netting or floodlights will be chargeable."
    )
    
    featured_image = models.ImageField(upload_to='turf_images/', blank=True, null=True)
    is_demo = models.BooleanField(default=False, help_text="Flag for demonstration listing in mini-project")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.area}, {self.city}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.name}-{self.area}")
            slug = base_slug
            counter = 1
            while Turf.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_sports_list(self):
        return [s.strip() for s in self.available_sports.split(',') if s.strip()]

    def get_facilities_list(self):
        return [f.strip() for f in self.facilities.split(',') if f.strip()]

    def average_rating(self):
        avg = self.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0.0

    def total_reviews(self):
        return self.reviews.filter(is_approved=True).count()


class TurfImage(models.Model):
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='turf_gallery/')
    caption = models.CharField(max_length=150, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.turf.name}"


class BlockedSlot(models.Model):
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='blocked_slots')
    block_date = models.DateField()
    start_time = models.TimeField(blank=True, null=True, help_text="Leave blank to block full day")
    end_time = models.TimeField(blank=True, null=True, help_text="Leave blank to block full day")
    reason = models.CharField(max_length=200, default='Maintenance / Private Event')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-block_date', 'start_time']

    def __str__(self):
        time_str = f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}" if self.start_time and self.end_time else "Full Day"
        return f"{self.turf.name} Blocked on {self.block_date} ({time_str})"


class Review(models.Model):
    turf = models.ForeignKey(Turf, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='turf_review', null=True, blank=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='turf_reviews')
    rating = models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], default=5)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.username}'s {self.rating}-star review for {self.turf.name}"

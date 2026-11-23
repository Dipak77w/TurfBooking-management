import os
import random
from datetime import datetime, date, time, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from accounts.models import UserProfile
from turfs.models import Turf, TurfImage, Review
from bookings.models import Booking, Payment


def generate_turf_graphic(filename, title, subtitle, color_primary=(22, 132, 71)):
    """Generates an aesthetic high-contrast sports turf graphic with field markings using Pillow."""
    width, height = 800, 480
    image = Image.new('RGB', (width, height), color=(16, 42, 67))
    draw = ImageDraw.Draw(image)

    # Gradient pitch stripes
    for y in range(0, height, 40):
        stripe_color = color_primary if (y // 40) % 2 == 0 else (
            max(0, color_primary[0] - 15),
            max(0, color_primary[1] - 15),
            max(0, color_primary[2] - 15)
        )
        draw.rectangle([0, y, width, y + 40], fill=stripe_color)

    # White pitch lines
    draw.rectangle([30, 30, width - 30, height - 30], outline=(255, 255, 255), width=4)
    # Center line
    draw.line([(width // 2, 30), (width // 2, height - 30)], fill=(255, 255, 255), width=3)
    # Center circle
    draw.ellipse([(width // 2 - 70, height // 2 - 70), (width // 2 + 70, height // 2 + 70)], outline=(255, 255, 255), width=3)
    # Penalty boxes
    draw.rectangle([30, height // 2 - 90, 160, height // 2 + 90], outline=(255, 255, 255), width=3)
    draw.rectangle([width - 160, height // 2 - 90, width - 30, height // 2 + 90], outline=(255, 255, 255), width=3)

    # Semi-transparent dark overlay card in center
    overlay_x1, overlay_y1 = 80, height // 2 - 75
    overlay_x2, overlay_y2 = width - 80, height // 2 + 75
    draw.rectangle([overlay_x1, overlay_y1, overlay_x2, overlay_y2], fill=(16, 42, 67), outline=(245, 166, 35), width=3)

    # Text rendering
    draw.text((width // 2, height // 2 - 35), title, fill=(255, 255, 255), anchor="mm")
    draw.text((width // 2, height // 2 + 5), subtitle, fill=(245, 166, 35), anchor="mm")
    draw.text((width // 2, height // 2 + 40), "Chhatrapati Sambhajinagar, Maharashtra • Demonstration Venue", fill=(216, 226, 220), anchor="mm")

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    image.save(filename, format='JPEG', quality=95)
    return filename


def generate_upi_qr_graphic(filename, upi_id="citysports@okhdfcbank"):
    """Generates an aesthetic UPI QR graphic with realistic positioning markers."""
    size = 400
    image = Image.new('RGB', (size, size), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Border
    draw.rectangle([10, 10, size - 10, size - 10], outline=(16, 42, 67), width=4)

    # QR Corner markers
    def draw_marker(x, y):
        draw.rectangle([x, y, x + 80, y + 80], fill=(16, 42, 67))
        draw.rectangle([x + 15, y + 15, x + 65, y + 65], fill=(255, 255, 255))
        draw.rectangle([x + 25, y + 25, x + 55, y + 55], fill=(22, 132, 71))

    draw_marker(30, 30)
    draw_marker(size - 110, 30)
    draw_marker(30, size - 110)

    # Random data grid imitation
    random.seed(42)
    step = 16
    for i in range(120, size - 120, step):
        for j in range(30, size - 30, step):
            if random.random() > 0.5:
                draw.rectangle([i, j, i + step - 2, j + step - 2], fill=(16, 42, 67))

    for i in range(30, size - 30, step):
        for j in range(120, size - 120, step):
            if (i < 110 and j < 110) or (i > size - 110 and j < 110) or (i < 110 and j > size - 110):
                continue
            if random.random() > 0.5:
                color = (22, 132, 71) if random.random() > 0.6 else (16, 42, 67)
                draw.rectangle([i, j, i + step - 2, j + step - 2], fill=color)

    # Center Logo badge
    cx, cy = size // 2, size // 2
    draw.rectangle([cx - 45, cy - 25, cx + 45, cy + 25], fill=(255, 255, 255), outline=(22, 132, 71), width=2)
    draw.text((cx, cy - 8), "BHIM UPI", fill=(16, 42, 67), anchor="mm")
    draw.text((cx, cy + 10), "VERIFIED", fill=(22, 132, 71), anchor="mm")

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    image.save(filename, format='PNG')
    return filename


class Command(BaseCommand):
    help = 'Seeds demonstration turfs, demo users, bookings, payments and realistic media.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding MiniTurf Arena demo data..."))

        # 1. Create Media Graphics
        media_root = settings.MEDIA_ROOT
        turf_images_dir = os.path.join(media_root, 'turf_images')
        upi_qr_dir = os.path.join(media_root, 'upi_qr')
        os.makedirs(turf_images_dir, exist_ok=True)
        os.makedirs(upi_qr_dir, exist_ok=True)

        img1_path = os.path.join(turf_images_dir, 'city_sports_arena.jpg')
        img2_path = os.path.join(turf_images_dir, 'champion_box_cricket.jpg')
        img3_path = os.path.join(turf_images_dir, 'greenfield_football.jpg')
        qr_path = os.path.join(upi_qr_dir, 'owner_upi_qr.png')

        generate_turf_graphic(img1_path, "CITY SPORTS ARENA", "MULTI-SPORT ARENA (FOOTBALL & CRICKET)", (22, 132, 71))
        generate_turf_graphic(img2_path, "CHAMPION BOX CRICKET TURF", "PROFESSIONAL ENCLOSED SYNTHETIC TURF", (30, 100, 150))
        generate_turf_graphic(img3_path, "GREENFIELD FOOTBALL TURF", "FIFA-STANDARD 7v7 / 5v5 FOOTBALL PITCH", (18, 120, 60))
        generate_upi_qr_graphic(qr_path, "citysports@okhdfcbank")

        # 2. Create Users
        # A. Turf Owner (Admin)
        owner_user, _ = User.objects.get_or_create(
            username='owner',
            defaults={
                'email': 'owner@miniturfarena.com',
                'first_name': 'Sanjay',
                'last_name': 'Patil',
                'is_staff': True
            }
        )
        owner_user.set_password('owner1234')
        owner_user.save()

        owner_profile, _ = UserProfile.objects.get_or_create(user=owner_user)
        owner_profile.role = 'OWNER'
        owner_profile.business_name = 'Sambhajinagar Sports Arenas Ltd.'
        owner_profile.phone = '+91 98765 43210'
        owner_profile.city = 'Chhatrapati Sambhajinagar'
        owner_profile.address = 'Cannaught Commercial Complex, CIDCO, Chhatrapati Sambhajinagar'
        owner_profile.upi_id = 'citysports@okhdfcbank'
        owner_profile.upi_qr_image = 'upi_qr/owner_upi_qr.png'
        owner_profile.save()

        # B. Customer (Player)
        customer_user, _ = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@miniturfarena.com',
                'first_name': 'Rahul',
                'last_name': 'Deshmukh'
            }
        )
        customer_user.set_password('cust1234')
        customer_user.save()

        customer_profile, _ = UserProfile.objects.get_or_create(user=customer_user)
        customer_profile.role = 'CUSTOMER'
        customer_profile.phone = '+91 98220 12345'
        customer_profile.city = 'Chhatrapati Sambhajinagar'
        customer_profile.address = 'Shivaji Nagar, Jalna Road, Chhatrapati Sambhajinagar'
        customer_profile.save()

        # C. Django Superuser
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@miniturfarena.com',
                'first_name': 'Super',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin_user.set_password('admin1234')
        admin_user.save()

        # 3. Create the 3 Realistic Demonstration Turfs from Chhatrapati Sambhajinagar
        # Turf 1: City Sports Arena
        t1, _ = Turf.objects.update_or_create(
            slug='city-sports-arena-cidco',
            defaults={
                'owner': owner_user,
                'name': 'City Sports Arena',
                'city': 'Chhatrapati Sambhajinagar',
                'area': 'CIDCO Cannaught Place',
                'address': 'Plot 14, Commercial Zone, Near Cannaught Garden, CIDCO N-4, Chhatrapati Sambhajinagar, MH 431003',
                'google_maps_url': 'https://maps.google.com/?q=CIDCO+Cannaught+Place+Chhatrapati+Sambhajinagar',
                'turf_type': 'Multi-Sport Arena',
                'size': '110 x 65 ft (Multi-Sport Standard)',
                'available_sports': 'Football, Box Cricket, Cricket, Badminton',
                'hourly_price': 900.00,
                'opening_time': time(6, 0),
                'closing_time': time(23, 0),
                'slot_duration_minutes': 60,
                'facilities': 'Floodlights, Parking, Washroom, Changing Room, Drinking Water, Cafeteria, First Aid',
                'contact_number': '+91 98221 44556',
                'description': (
                    "Premier multi-sport arena in the heart of CIDCO Cannaught Place. Features European 50mm "
                    "monofilament shock-absorbent synthetic grass engineered for both football studs and rapid "
                    "box cricket. Equipped with 8 high-mast glare-free LED floodlights for crisp night vision, "
                    "player dugouts, dedicated air-cooled changing rooms, and RO chilled drinking water."
                ),
                'featured_image': 'turf_images/city_sports_arena.jpg',
                'is_demo': True,
                'is_active': True
            }
        )

        # Turf 2: Champion Box Cricket Turf
        t2, _ = Turf.objects.update_or_create(
            slug='champion-box-cricket-turf-beed-bypass',
            defaults={
                'owner': owner_user,
                'name': 'Champion Box Cricket Turf',
                'city': 'Chhatrapati Sambhajinagar',
                'area': 'Beed Bypass Road',
                'address': 'Opposite MIT College Ground, Beed Bypass Road, Chhatrapati Sambhajinagar, MH 431005',
                'google_maps_url': 'https://maps.google.com/?q=Beed+Bypass+Chhatrapati+Sambhajinagar',
                'turf_type': 'Box Cricket',
                'size': '95 x 55 ft (Enclosed High-Tension Net)',
                'available_sports': 'Box Cricket, Cricket',
                'hourly_price': 750.00,
                'opening_time': time(6, 0),
                'closing_time': time(23, 30),
                'slot_duration_minutes': 60,
                'facilities': 'Floodlights, Parking, Drinking Water, Washroom, Seating Dugout, Equipment Rental',
                'contact_number': '+91 98902 33441',
                'description': (
                    "Specially designed high-tension roof-netted box cricket arena on Beed Bypass. Dense 40mm "
                    "anti-skid synthetic turf with precise bowling crease markings. Complete with professional "
                    "leather and tennis ball bowling nets, boundary rope sensors, and stadium-style spectator seating."
                ),
                'featured_image': 'turf_images/champion_box_cricket.jpg',
                'is_demo': True,
                'is_active': True
            }
        )

        # Turf 3: Greenfield Football Turf
        t3, _ = Turf.objects.update_or_create(
            slug='greenfield-football-turf-seven-hills',
            defaults={
                'owner': owner_user,
                'name': 'Greenfield Football Turf',
                'city': 'Chhatrapati Sambhajinagar',
                'area': 'Seven Hills, Jalna Road',
                'address': 'Survey 82, Near Seven Hills Flyover, Jalna Road, Chhatrapati Sambhajinagar, MH 431001',
                'google_maps_url': 'https://maps.google.com/?q=Seven+Hills+Jalna+Road+Chhatrapati+Sambhajinagar',
                'turf_type': 'Football',
                'size': '130 x 85 ft (7-A-Side & 5-A-Side)',
                'available_sports': 'Football',
                'hourly_price': 1100.00,
                'opening_time': time(5, 30),
                'closing_time': time(23, 0),
                'slot_duration_minutes': 60,
                'facilities': 'Floodlights, Parking, Changing Room, Washroom, Drinking Water, First Aid, Locker Rooms',
                'contact_number': '+91 94227 88990',
                'description': (
                    "FIFA-preferred 2-star certified artificial grass football pitch with natural silica infill "
                    "and rubber granules. Optimal for 7v7 and 5v5 competitive leagues. Includes regulation aluminum "
                    "goalposts, perimeter safety netting, electronic scoreboard, and certified medical first-aid kit on site."
                ),
                'featured_image': 'turf_images/greenfield_football.jpg',
                'is_demo': True,
                'is_active': True
            }
        )

        # 4. Sample Bookings & Payments for Demonstration
        today = timezone.localdate()
        
        # Booking 1: Upcoming Confirmed Booking for Customer tomorrow
        tomorrow = today + timedelta(days=1)
        b1, _ = Booking.objects.get_or_create(
            booking_id='TRF-202611-DEMO1',
            defaults={
                'turf': t1,
                'customer': customer_user,
                'sport': 'Football',
                'booking_date': tomorrow,
                'start_time': time(18, 0),
                'end_time': time(19, 0),
                'total_price': 900.00,
                'player_name': 'Rahul Deshmukh',
                'player_phone': '+91 98220 12345',
                'player_email': 'customer@miniturfarena.com',
                'special_notes': 'Need extra bibs for 5v5 match.',
                'status': 'CONFIRMED'
            }
        )
        Payment.objects.get_or_create(
            booking=b1,
            defaults={
                'amount': 900.00,
                'upi_reference_id': '432190887612',
                'payment_method': 'UPI QR Scanner',
                'status': 'PAID',
                'verified_by': owner_user,
                'verified_at': timezone.now()
            }
        )

        # Booking 2: Pending Payment Verification for Owner Dashboard Demo
        b2, _ = Booking.objects.get_or_create(
            booking_id='TRF-202611-DEMO2',
            defaults={
                'turf': t2,
                'customer': customer_user,
                'sport': 'Box Cricket',
                'booking_date': today + timedelta(days=2),
                'start_time': time(20, 0),
                'end_time': time(21, 0),
                'total_price': 750.00,
                'player_name': 'Vikram Jadhav',
                'player_phone': '+91 98234 56789',
                'status': 'PENDING'
            }
        )
        Payment.objects.get_or_create(
            booking=b2,
            defaults={
                'amount': 750.00,
                'upi_reference_id': '432981002341',
                'payment_method': 'UPI QR Scanner',
                'status': 'PENDING'
            }
        )

        # Booking 3: Past Completed Match
        yesterday = today - timedelta(days=2)
        b3, _ = Booking.objects.get_or_create(
            booking_id='TRF-202611-DEMO3',
            defaults={
                'turf': t3,
                'customer': customer_user,
                'sport': 'Football',
                'booking_date': yesterday,
                'start_time': time(19, 0),
                'end_time': time(20, 0),
                'total_price': 1100.00,
                'player_name': 'Rahul Deshmukh',
                'player_phone': '+91 98220 12345',
                'status': 'COMPLETED'
            }
        )
        Payment.objects.get_or_create(
            booking=b3,
            defaults={
                'amount': 1100.00,
                'upi_reference_id': '431098234567',
                'payment_method': 'UPI QR Scanner',
                'status': 'PAID',
                'verified_by': owner_user,
                'verified_at': timezone.now() - timedelta(days=2)
            }
        )

        # 5. Sample Reviews for the turfs
        Review.objects.get_or_create(
            turf=t1,
            customer=customer_user,
            defaults={
                'booking': b3,
                'rating': 5,
                'comment': 'Outstanding turf quality and lighting! The floodlights are bright with zero glare, and parking was very convenient in CIDCO.',
                'is_approved': True
            }
        )
        Review.objects.get_or_create(
            turf=t2,
            customer=customer_user,
            defaults={
                'rating': 5,
                'comment': 'Best box cricket experience on Beed Bypass. The roof netting is high and boundary bounce is consistent.',
                'is_approved': True
            }
        )
        Review.objects.get_or_create(
            turf=t3,
            customer=customer_user,
            defaults={
                'rating': 5,
                'comment': 'FIFA standard grass feels awesome for football studs. Changing rooms and drinking water are top notch.',
                'is_approved': True
            }
        )

        self.stdout.write(self.style.SUCCESS("Demo data successfully seeded!"))
        self.stdout.write(self.style.SUCCESS("Demo Credentials:"))
        self.stdout.write("  - Customer: customer / cust1234")
        self.stdout.write("  - Turf Owner (Admin): owner / owner1234")
        self.stdout.write("  - Superuser: admin / admin1234")

from datetime import datetime, date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponse, JsonResponse

from turfs.models import Turf, BlockedSlot, Review
from turfs.forms import ReviewForm
from .models import Booking, Payment
from .forms import BookingForm, PaymentSubmissionForm
from accounts.decorators import customer_required, owner_required


@login_required
@customer_required
def initiate_booking_view(request, slug):
    """
    Step 1 of Booking:
    Validates slot selection, checks for concurrency collisions, and creates a PENDING booking.
    """
    turf = get_object_or_404(Turf, slug=slug, is_active=True)

    if request.method == 'POST':
        form = BookingForm(request.POST)
        
        # Populate sport choices dynamically
        sports = turf.get_sports_list()
        form.fields['sport'].widget.choices = [(s, s) for s in sports]

        if form.is_valid():
            booking_date = form.cleaned_data['booking_date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            sport = form.cleaned_data['sport']
            player_name = form.cleaned_data['player_name']
            player_phone = form.cleaned_data['player_phone']
            player_email = form.cleaned_data['player_email']
            special_notes = form.cleaned_data['special_notes']

            today = timezone.localdate()
            now = timezone.localtime(timezone.now())

            # 1. Past date check
            if booking_date < today:
                messages.error(request, "Cannot book slots in the past.")
                return redirect('turf_detail', slug=turf.slug)

            # 2. Past time check if today
            if booking_date == today:
                slot_aware_dt = timezone.make_aware(
                    datetime.combine(booking_date, start_time), 
                    timezone.get_current_timezone()
                )
                if slot_aware_dt <= now:
                    messages.error(request, "This time slot has already passed. Please select an upcoming slot.")
                    return redirect('turf_detail', slug=turf.slug)

            # 3. Check blocked slots
            is_blocked = BlockedSlot.objects.filter(
                turf=turf,
                block_date=booking_date
            ).filter(
                Q(start_time__isnull=True) |
                (Q(start_time__lt=end_time) & Q(end_time__gt=start_time))
            ).exists()

            if is_blocked:
                messages.error(request, "This slot has been blocked by the turf management for maintenance.")
                return redirect('turf_detail', slug=turf.slug)

            # 4. Concurrency & Double-Booking Protection using DB transaction
            try:
                with transaction.atomic():
                    # Check if an active booking already exists
                    conflict_exists = Booking.objects.select_for_update().filter(
                        turf=turf,
                        booking_date=booking_date,
                        start_time=start_time,
                        status__in=['CONFIRMED', 'PENDING']
                    ).exists()

                    if conflict_exists:
                        messages.error(request, "Sorry! This time slot was just booked by another player. Please select another slot.")
                        return redirect('turf_detail', slug=turf.slug)

                    # Calculate price
                    total_price = turf.hourly_price

                    # Create Booking
                    booking = form.save(commit=False)
                    booking.turf = turf
                    booking.customer = request.user
                    booking.total_price = total_price
                    booking.status = 'PENDING'
                    booking.save()

                    # Create corresponding Payment record
                    Payment.objects.create(
                        booking=booking,
                        amount=total_price,
                        status='PENDING'
                    )

                messages.info(request, f"Slot temporarily reserved! Please complete the UPI payment to confirm your booking.")
                return redirect('checkout_payment', booking_id=booking.booking_id)

            except Exception as e:
                messages.error(request, f"An unexpected error occurred while reserving the slot: {str(e)}")
                return redirect('turf_detail', slug=turf.slug)
        else:
            messages.error(request, "Please check the booking form fields.")
            return redirect('turf_detail', slug=turf.slug)

    return redirect('turf_detail', slug=turf.slug)


@login_required
@customer_required
def checkout_payment_view(request, booking_id):
    """
    Step 2: UPI QR Payment submission page.
    Shows the owner's UPI QR code, UPI ID, total amount, and accepts transaction ID + screenshot.
    """
    booking = get_object_or_404(Booking, booking_id=booking_id, customer=request.user)
    payment = booking.payment

    # Owner's UPI details
    owner_profile = getattr(booking.turf.owner, 'profile', None)
    upi_id = owner_profile.upi_id if (owner_profile and owner_profile.upi_id) else 'citysports@upi'
    upi_qr_url = owner_profile.upi_qr_image.url if (owner_profile and owner_profile.upi_qr_image) else None

    if request.method == 'POST':
        # Check if demo quick submit is pressed
        if 'demo_submit' in request.POST:
            sample_utr = f"UPI{int(timezone.now().timestamp())}"
            payment.upi_reference_id = sample_utr
            payment.status = 'PENDING'
            payment.save()
            messages.success(request, f"Demo payment submitted with reference ID: {sample_utr}! Status is now Pending Verification.")
            return redirect('customer_dashboard')

        form = PaymentSubmissionForm(request.POST, request.FILES, instance=payment)
        if form.is_valid():
            p = form.save(commit=False)
            p.status = 'PENDING'
            p.save()
            messages.success(request, "Payment proof submitted successfully! Turf owner will verify your transaction shortly.")
            return redirect('customer_dashboard')
        else:
            messages.error(request, "Please enter a valid UPI reference ID.")
    else:
        form = PaymentSubmissionForm(instance=payment)

    context = {
        'booking': booking,
        'payment': payment,
        'turf': booking.turf,
        'upi_id': upi_id,
        'upi_qr_url': upi_qr_url,
        'form': form,
        'title': f'Complete Payment - {booking.booking_id}',
    }
    return render(request, 'bookings/checkout_payment.html', context)


@login_required
@customer_required
def cancel_booking_view(request, booking_id):
    """
    Enforces the 30-minute cancellation policy.
    Releases slot if eligible.
    """
    booking = get_object_or_404(Booking, booking_id=booking_id, customer=request.user)
    
    can_cancel, reason = booking.can_cancel()
    
    if request.method == 'POST':
        if not can_cancel:
            messages.error(request, f"Cancellation Denied: {reason}")
            return redirect('customer_dashboard')

        cancel_reason = request.POST.get('cancellation_reason', 'Cancelled by player')
        booking.status = 'CANCELLED'
        booking.cancellation_reason = cancel_reason
        booking.cancelled_at = timezone.now()
        booking.save()

        # Update payment status if needed
        if hasattr(booking, 'payment'):
            if booking.payment.status != 'PAID':
                booking.payment.status = 'REJECTED'
                booking.payment.rejection_reason = 'Booking Cancelled by customer'
                booking.payment.save()

        messages.success(request, f"Booking {booking.booking_id} has been cancelled successfully. The slot has been released for other players.")
        return redirect('customer_dashboard')

    context = {
        'booking': booking,
        'can_cancel': can_cancel,
        'reason': reason,
        'title': f'Cancel Booking - {booking.booking_id}'
    }
    return render(request, 'bookings/cancel_confirm.html', context)


@login_required
def booking_receipt_view(request, booking_id):
    """
    Printable booking receipt / invoice for the customer or owner.
    """
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # Permission check: customer of booking, or owner of turf, or superuser
    if request.user != booking.customer and request.user != booking.turf.owner and not request.user.is_superuser:
        messages.error(request, "You do not have permission to view this receipt.")
        return redirect('home')

    context = {
        'booking': booking,
        'payment': getattr(booking, 'payment', None),
        'turf': booking.turf,
        'title': f'Receipt - {booking.booking_id}'
    }
    return render(request, 'bookings/receipt.html', context)


@login_required
@customer_required
def customer_dashboard_view(request):
    """
    Customer Dashboard:
    - Upcoming Bookings
    - Completed / Past Bookings
    - Cancelled Bookings
    - Leave Review option
    """
    user = request.user
    all_bookings = Booking.objects.filter(customer=user).select_related('turf', 'payment')

    now = timezone.now()

    upcoming_bookings = []
    past_bookings = []
    cancelled_bookings = []

    for b in all_bookings:
        if b.status == 'CANCELLED' or b.status == 'REJECTED':
            cancelled_bookings.append(b)
        elif b.is_past or b.status == 'COMPLETED':
            past_bookings.append(b)
        else:
            upcoming_bookings.append(b)

    # Customer profile stats
    total_spent = all_bookings.filter(payment__status='PAID').aggregate(Sum('total_price'))['total_price__sum'] or 0

    context = {
        'user': user,
        'profile': user.profile,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'cancelled_bookings': cancelled_bookings,
        'total_bookings_count': all_bookings.count(),
        'confirmed_count': all_bookings.filter(status='CONFIRMED').count(),
        'total_spent': total_spent,
        'title': 'Customer Dashboard - MiniTurf Arena'
    }
    return render(request, 'bookings/customer_dashboard.html', context)


@login_required
@customer_required
def submit_review_view(request, booking_id):
    """Submit a rating & review after completing a booking."""
    booking = get_object_or_404(Booking, booking_id=booking_id, customer=request.user)

    if booking.status not in ['CONFIRMED', 'COMPLETED'] and not booking.is_past:
        messages.error(request, "Reviews can only be submitted for completed or confirmed bookings.")
        return redirect('customer_dashboard')

    if hasattr(booking, 'turf_review'):
        messages.warning(request, "You have already submitted a review for this booking.")
        return redirect('customer_dashboard')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.turf = booking.turf
            review.customer = request.user
            review.booking = booking
            review.save()
            messages.success(request, f"Thank you for rating {booking.turf.name}! Your review is now live.")
            return redirect('customer_dashboard')
        else:
            messages.error(request, "Please provide a valid rating.")
    else:
        form = ReviewForm()

    context = {
        'booking': booking,
        'turf': booking.turf,
        'form': form,
        'title': f'Review {booking.turf.name}'
    }
    return render(request, 'bookings/submit_review.html', context)


@login_required
@owner_required
def owner_dashboard_view(request):
    """
    Comprehensive Turf Owner Dashboard:
    - Real-time KPIs
    - Chart.js analytics data (Daily bookings, Monthly earnings, Status distribution)
    - Turf list & actions
    - Booking list & management
    - Payment verifications with screenshot modal
    - Reviews management
    """
    owner = request.user
    my_turfs = Turf.objects.filter(owner=owner)
    my_turf_ids = my_turfs.values_list('id', flat=True)

    all_bookings = Booking.objects.filter(turf_id__in=my_turf_ids).select_related('turf', 'customer', 'payment')
    today = timezone.localdate()

    # KPI Calculations
    total_turfs = my_turfs.count()
    total_bookings = all_bookings.count()
    today_bookings = all_bookings.filter(booking_date=today).count()
    
    pending_payments = Payment.objects.filter(
        booking__turf_id__in=my_turf_ids, 
        status='PENDING'
    ).select_related('booking', 'booking__turf', 'booking__customer')
    pending_count = pending_payments.count()

    confirmed_bookings_count = all_bookings.filter(status='CONFIRMED').count()
    cancelled_bookings_count = all_bookings.filter(status='CANCELLED').count()
    
    total_revenue = Payment.objects.filter(
        booking__turf_id__in=my_turf_ids, 
        status='PAID'
    ).aggregate(Sum('amount'))['amount__sum'] or 0.0

    # Recent booking activity (latest 10)
    recent_bookings = all_bookings.order_by('-created_at')[:10]

    # Analytics for Chart.js
    # 1. Daily bookings for past 7 days
    daily_labels = []
    daily_counts = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        daily_labels.append(d.strftime('%d %b'))
        cnt = all_bookings.filter(booking_date=d).count()
        daily_counts.append(cnt)

    # 2. Status distribution for Donut Chart
    status_counts = {
        'Confirmed': confirmed_bookings_count,
        'Pending': all_bookings.filter(status='PENDING').count(),
        'Cancelled': cancelled_bookings_count,
        'Rejected': all_bookings.filter(status='REJECTED').count(),
    }

    # 3. Monthly revenue (last 4 months)
    revenue_labels = []
    revenue_data = []
    for m in range(3, -1, -1):
        # approximate month start
        month_dt = today - timedelta(days=m * 30)
        label = month_dt.strftime('%b %Y')
        revenue_labels.append(label)
        rev = Payment.objects.filter(
            booking__turf_id__in=my_turf_ids,
            status='PAID',
            created_at__year=month_dt.year,
            created_at__month=month_dt.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        revenue_data.append(float(rev))

    # All customer reviews for owner's turfs
    reviews = Review.objects.filter(turf_id__in=my_turf_ids).select_related('turf', 'customer').order_by('-created_at')

    context = {
        'my_turfs': my_turfs,
        'total_turfs': total_turfs,
        'total_bookings': total_bookings,
        'today_bookings': today_bookings,
        'pending_payments': pending_payments,
        'pending_count': pending_count,
        'confirmed_count': confirmed_bookings_count,
        'cancelled_count': cancelled_bookings_count,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'all_bookings': all_bookings,
        'reviews': reviews,
        'daily_labels': daily_labels,
        'daily_counts': daily_counts,
        'status_labels': list(status_counts.keys()),
        'status_counts': list(status_counts.values()),
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'title': 'Turf Owner Admin Dashboard'
    }
    return render(request, 'bookings/owner_dashboard.html', context)


@login_required
@owner_required
def verify_payment_action(request, payment_id):
    """Admin action to approve or reject customer payment."""
    payment = get_object_or_404(Payment, id=payment_id)
    turf = payment.booking.turf

    if turf.owner != request.user and not request.user.is_superuser:
        messages.error(request, "Unauthorized.")
        return redirect('owner_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action') # 'approve' or 'reject'
        
        if action == 'approve':
            payment.status = 'PAID'
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()

            booking = payment.booking
            booking.status = 'CONFIRMED'
            booking.save()

            messages.success(request, f"Payment for booking {booking.booking_id} verified & confirmed successfully!")
        
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', 'Transaction reference could not be verified in bank records.')
            payment.status = 'REJECTED'
            payment.rejection_reason = reason
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()

            booking = payment.booking
            booking.status = 'REJECTED'
            booking.save()

            messages.warning(request, f"Payment for booking {booking.booking_id} was rejected. Slot has been released.")

    return redirect('owner_dashboard')


@login_required
@owner_required
def admin_booking_action(request, booking_id):
    """Allows owner to manually confirm, reject, or mark booking as completed."""
    booking = get_object_or_404(Booking, booking_id=booking_id)
    turf = booking.turf

    if turf.owner != request.user and not request.user.is_superuser:
        messages.error(request, "Unauthorized.")
        return redirect('owner_dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'confirm':
            booking.status = 'CONFIRMED'
            if hasattr(booking, 'payment'):
                booking.payment.status = 'PAID'
                booking.payment.verified_by = request.user
                booking.payment.verified_at = timezone.now()
                booking.payment.save()
            booking.save()
            messages.success(request, f"Booking {booking.booking_id} confirmed!")
        elif action == 'cancel':
            booking.status = 'CANCELLED'
            booking.cancellation_reason = 'Cancelled by Turf Management'
            booking.cancelled_at = timezone.now()
            booking.save()
            messages.info(request, f"Booking {booking.booking_id} cancelled.")
        elif action == 'complete':
            booking.status = 'COMPLETED'
            booking.save()
            messages.success(request, f"Booking {booking.booking_id} marked as Completed.")

    return redirect('owner_dashboard')

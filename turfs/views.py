from datetime import datetime, date
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg
from django.utils import timezone
from .models import Turf, TurfImage, BlockedSlot, Review
from .forms import TurfForm, TurfImageForm, BlockedSlotForm, ReviewForm
from .slot_utils import generate_turf_slots
from accounts.decorators import owner_required, customer_required


def turf_list_view(request):
    """Explore and filter all available turfs."""
    turfs = Turf.objects.filter(is_active=True)

    # Search query
    q = request.GET.get('q', '').strip()
    if q:
        turfs = turfs.filter(
            Q(name__icontains=q) | 
            Q(area__icontains=q) | 
            Q(city__icontains=q) |
            Q(available_sports__icontains=q)
        )

    # Sport filter
    sport = request.GET.get('sport', '').strip()
    if sport:
        turfs = turfs.filter(available_sports__icontains=sport)

    # Turf type filter
    turf_type = request.GET.get('turf_type', '').strip()
    if turf_type:
        turfs = turfs.filter(turf_type=turf_type)

    # Max price filter
    max_price = request.GET.get('max_price', '').strip()
    if max_price:
        try:
            turfs = turfs.filter(hourly_price__lte=float(max_price))
        except ValueError:
            pass

    # Sort
    sort = request.GET.get('sort', 'popular')
    if sort == 'price_low':
        turfs = turfs.order_by('hourly_price')
    elif sort == 'price_high':
        turfs = turfs.order_by('-hourly_price')
    else:
        turfs = turfs.order_by('-created_at')

    # Popular sports for filter pill buttons
    sports_options = ['Football', 'Box Cricket', 'Cricket', 'Badminton', 'Tennis', 'Volleyball']

    context = {
        'turfs': turfs,
        'title': 'Explore Turfs in Chhatrapati Sambhajinagar',
        'q': q,
        'selected_sport': sport,
        'selected_type': turf_type,
        'selected_price': max_price,
        'selected_sort': sort,
        'sports_options': sports_options,
        'turf_type_choices': Turf.TURF_TYPE_CHOICES,
    }
    return render(request, 'turfs/turf_list.html', context)


def turf_detail_view(request, slug):
    """Detailed view for a specific turf with gallery, reviews, and interactive slot picker."""
    turf = get_object_or_404(Turf, slug=slug, is_active=True)
    reviews = turf.reviews.filter(is_approved=True)
    images = turf.images.all()

    # Default booking date is today
    today = timezone.localdate()
    default_date_str = today.strftime('%Y-%m-%d')
    
    # Generate initial slots for today
    initial_slots = generate_turf_slots(turf, today)

    context = {
        'turf': turf,
        'reviews': reviews,
        'images': images,
        'today_date': default_date_str,
        'initial_slots': initial_slots,
        'title': f"{turf.name} - MiniTurf Arena",
    }
    return render(request, 'turfs/turf_detail.html', context)


def api_get_slots_view(request, slug):
    """AJAX endpoint to fetch dynamic time slots for a given date."""
    turf = get_object_or_404(Turf, slug=slug, is_active=True)
    date_str = request.GET.get('date', '')

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

    # Disallow dates in the past
    today = timezone.localdate()
    if target_date < today:
        return JsonResponse({'error': 'Cannot check slots for past dates.'}, status=400)

    slots = generate_turf_slots(turf, target_date)
    return JsonResponse({
        'turf_id': turf.id,
        'date': date_str,
        'hourly_price': float(turf.hourly_price),
        'slots': slots
    })


@login_required
@owner_required
def add_turf_view(request):
    """Add a new turf listing by turf owner."""
    if request.method == 'POST':
        form = TurfForm(request.POST, request.FILES)
        if form.is_valid():
            turf = form.save(commit=False)
            turf.owner = request.user
            turf.save()
            messages.success(request, f'Turf "{turf.name}" has been created successfully!')
            return redirect('owner_dashboard')
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        form = TurfForm()

    context = {
        'form': form,
        'title': 'Add New Turf Listing',
        'action': 'Add'
    }
    return render(request, 'turfs/turf_form.html', context)


@login_required
@owner_required
def edit_turf_view(request, slug):
    """Edit an existing turf owned by the logged-in owner."""
    turf = get_object_or_404(Turf, slug=slug)
    
    # Ownership verification
    if turf.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied: You can only edit turfs you own.')
        return redirect('owner_dashboard')

    if request.method == 'POST':
        form = TurfForm(request.POST, request.FILES, instance=turf)
        if form.is_valid():
            form.save()
            messages.success(request, f'Turf "{turf.name}" has been updated successfully!')
            return redirect('owner_dashboard')
        else:
            messages.error(request, 'Please review the errors in the form.')
    else:
        form = TurfForm(instance=turf)

    context = {
        'form': form,
        'turf': turf,
        'title': f'Edit Turf: {turf.name}',
        'action': 'Edit'
    }
    return render(request, 'turfs/turf_form.html', context)


@login_required
@owner_required
def delete_turf_view(request, slug):
    """Delete a turf owned by the logged-in owner."""
    turf = get_object_or_404(Turf, slug=slug)
    
    if turf.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied: You can only delete turfs you own.')
        return redirect('owner_dashboard')

    if request.method == 'POST':
        turf_name = turf.name
        turf.delete()
        messages.success(request, f'Turf "{turf_name}" was successfully deleted.')
        return redirect('owner_dashboard')

    return render(request, 'turfs/turf_confirm_delete.html', {'turf': turf, 'title': f'Delete {turf.name}'})


@login_required
@owner_required
def manage_turf_images_view(request, slug):
    """Upload and manage gallery images for a turf."""
    turf = get_object_or_404(Turf, slug=slug)
    if turf.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('owner_dashboard')

    if request.method == 'POST':
        form = TurfImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.turf = turf
            image.save()
            messages.success(request, 'Photo uploaded successfully!')
            return redirect('manage_turf_images', slug=slug)
    else:
        form = TurfImageForm()

    images = turf.images.all()
    context = {
        'turf': turf,
        'images': images,
        'form': form,
        'title': f'Manage Photos - {turf.name}'
    }
    return render(request, 'turfs/manage_images.html', context)


@login_required
@owner_required
def delete_turf_image_view(request, image_id):
    """Delete a specific turf gallery photo."""
    image = get_object_or_404(TurfImage, id=image_id)
    turf = image.turf
    if turf.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('owner_dashboard')

    image.delete()
    messages.success(request, 'Photo removed successfully.')
    return redirect('manage_turf_images', slug=turf.slug)


@login_required
@owner_required
def manage_blocked_slots_view(request, slug):
    """View and block dates/slots for maintenance or private events."""
    turf = get_object_or_404(Turf, slug=slug)
    if turf.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('owner_dashboard')

    if request.method == 'POST':
        form = BlockedSlotForm(request.POST)
        if form.is_valid():
            blocked = form.save(commit=False)
            blocked.turf = turf
            blocked.save()
            messages.success(request, 'Slot/Date successfully blocked.')
            return redirect('manage_blocked_slots', slug=slug)
    else:
        form = BlockedSlotForm()

    blocked_slots = turf.blocked_slots.all()
    context = {
        'turf': turf,
        'blocked_slots': blocked_slots,
        'form': form,
        'title': f'Block Dates & Slots - {turf.name}'
    }
    return render(request, 'turfs/manage_blocked_slots.html', context)


@login_required
@owner_required
def delete_blocked_slot_view(request, slot_id):
    """Unblock a slot/date."""
    slot = get_object_or_404(BlockedSlot, id=slot_id)
    turf = slot.turf
    if turf.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('owner_dashboard')

    slot.delete()
    messages.success(request, 'Blocked slot released.')
    return redirect('manage_blocked_slots', slug=turf.slug)


@login_required
@owner_required
def moderate_review_view(request, review_id):
    """Moderate / toggle visibility of customer review."""
    review = get_object_or_404(Review, id=review_id)
    if review.turf.owner != request.user and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('owner_dashboard')

    action = request.POST.get('action')
    if action == 'delete':
        review.delete()
        messages.success(request, 'Review has been removed.')
    elif action == 'toggle':
        review.is_approved = not review.is_approved
        review.save()
        messages.success(request, f'Review visibility updated to {"Visible" if review.is_approved else "Hidden"}.')

    return redirect('owner_dashboard')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg
from turfs.models import Turf, Review


def home_view(request):
    """
    Commercial-grade, modern sports homepage.
    """
    featured_turfs = Turf.objects.filter(is_active=True).order_by('-created_at')[:6]
    
    # Customer reviews for testimonials
    testimonials = Review.objects.filter(is_approved=True, rating__gte=4).select_related('turf', 'customer').order_by('-created_at')[:4]
    
    # Sports categories
    sports_categories = [
        {
            'name': 'Football',
            'icon': 'bi-futbol',
            'desc': '7v7 & 5v5 FIFA standard grass turfs with high floodlights.',
            'count': Turf.objects.filter(is_active=True, available_sports__icontains='Football').count()
        },
        {
            'name': 'Box Cricket',
            'icon': 'bi-trophy',
            'desc': 'Enclosed synthetic turf pitches ideal for high-speed box tournaments.',
            'count': Turf.objects.filter(is_active=True, available_sports__icontains='Box Cricket').count()
        },
        {
            'name': 'Cricket',
            'icon': 'bi-shield-shaded',
            'desc': 'Full-length turf wickets with bowling machines and nets.',
            'count': Turf.objects.filter(is_active=True, available_sports__icontains='Cricket').count()
        },
        {
            'name': 'Badminton',
            'icon': 'bi-grid-3x3',
            'desc': 'Indoor wooden & BWF-certified synthetic courts with AC/ventilation.',
            'count': Turf.objects.filter(is_active=True, available_sports__icontains='Badminton').count()
        },
    ]

    context = {
        'featured_turfs': featured_turfs,
        'testimonials': testimonials,
        'sports_categories': sports_categories,
        'title': 'Book Your Game. Play Your Passion.'
    }
    return render(request, 'core/home.html', context)


def about_view(request):
    return render(request, 'core/about.html', {'title': 'About MiniTurf Arena'})


def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        messages.success(request, f"Thank you, {name}! Your message has been received. Our support team will get back to you shortly.")
        return redirect('contact')
    return render(request, 'core/contact.html', {'title': 'Contact Us - MiniTurf Arena'})

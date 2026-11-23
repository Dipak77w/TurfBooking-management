from accounts.models import UserProfile
from bookings.models import Payment

def global_context(request):
    context = {
        'SITE_NAME': 'MiniTurf Arena',
        'SITE_CITY': 'Chhatrapati Sambhajinagar',
        'is_turf_owner': False,
        'is_customer': False,
        'user_profile': None,
        'pending_payments_badge_count': 0,
    }
    
    if request.user.is_authenticated:
        try:
            profile = request.user.profile
            context['user_profile'] = profile
            context['is_turf_owner'] = profile.is_owner
            context['is_customer'] = profile.is_customer
            
            if profile.is_owner:
                # Count pending payments for owner's turfs
                context['pending_payments_badge_count'] = Payment.objects.filter(
                    booking__turf__owner=request.user,
                    status='PENDING'
                ).count()
        except UserProfile.DoesNotExist:
            pass

    return context

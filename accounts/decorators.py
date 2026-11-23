from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def customer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access this page.")
            return redirect(f"{reverse('customer_login')}?next={request.path}")
        
        if hasattr(request.user, 'profile') and request.user.profile.is_owner:
            messages.info(request, "You are logged in as a Turf Owner. Please access the Admin Dashboard.")
            return redirect('owner_dashboard')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Turf Owner login required to access Admin Dashboard.")
            return redirect(f"{reverse('owner_login')}?next={request.path}")
        
        if not (hasattr(request.user, 'profile') and request.user.profile.is_owner) and not request.user.is_superuser:
            messages.error(request, "Access Denied: You do not have Turf Owner administrative privileges.")
            return redirect('customer_dashboard')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

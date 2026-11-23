from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import (
    CustomerRegistrationForm, 
    OwnerRegistrationForm, 
    CustomerProfileForm, 
    OwnerSettingsForm
)
from .models import UserProfile
from .decorators import customer_required, owner_required


def customer_login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.is_owner:
            return redirect('owner_dashboard')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if hasattr(user, 'profile') and user.profile.is_owner:
                messages.warning(request, "This account is a Turf Owner account. Please log in via Admin Login.")
                return redirect('owner_login')
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'customer_dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    context = {
        'form': form,
        'title': 'Customer Login',
        'is_customer_portal': True
    }
    return render(request, 'accounts/customer_login.html', context)


def owner_login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.is_owner:
            return redirect('owner_dashboard')
        messages.info(request, "You are logged in as a Customer. Log out first to switch to Owner account.")
        return redirect('customer_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not ((hasattr(user, 'profile') and user.profile.is_owner) or user.is_superuser):
                messages.error(request, "Access restricted: This account is registered as a customer, not a turf owner.")
                return render(request, 'accounts/owner_login.html', {'form': form, 'title': 'Turf Owner Login'})
            
            login(request, user)
            messages.success(request, f"Welcome to Turf Admin Portal, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            return redirect(next_url if next_url else 'owner_dashboard')
        else:
            messages.error(request, "Invalid admin credentials. Please check your username and password.")
    else:
        form = AuthenticationForm()

    context = {
        'form': form,
        'title': 'Turf Owner Admin Login',
        'is_owner_portal': True
    }
    return render(request, 'accounts/owner_login.html', context)


def customer_register_view(request):
    if request.user.is_authenticated:
        return redirect('customer_dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            full_name = form.cleaned_data['full_name'].strip().split(' ', 1)
            user.first_name = full_name[0]
            user.last_name = full_name[1] if len(full_name) > 1 else ''
            user.save()

            # Profile is auto-created by signal, update customer fields
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'CUSTOMER'
            profile.phone = form.cleaned_data['phone']
            profile.city = 'Chhatrapati Sambhajinagar'
            profile.save()

            login(request, user)
            messages.success(request, "Registration successful! Welcome to MiniTurf Arena.")
            return redirect('customer_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomerRegistrationForm()

    return render(request, 'accounts/customer_register.html', {'form': form, 'title': 'Customer Registration'})


def owner_register_view(request):
    if request.user.is_authenticated:
        return redirect('owner_dashboard')

    if request.method == 'POST':
        form = OwnerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            full_name = form.cleaned_data['full_name'].strip().split(' ', 1)
            user.first_name = full_name[0]
            user.last_name = full_name[1] if len(full_name) > 1 else ''
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'OWNER'
            profile.business_name = form.cleaned_data['business_name']
            profile.phone = form.cleaned_data['phone']
            profile.upi_id = form.cleaned_data.get('upi_id')
            if 'upi_qr_image' in request.FILES:
                profile.upi_qr_image = request.FILES['upi_qr_image']
            profile.save()

            login(request, user)
            messages.success(request, "Turf Owner account registered successfully! You can now list and manage turfs.")
            return redirect('owner_dashboard')
        else:
            messages.error(request, "Please correct the registration errors.")
    else:
        form = OwnerRegistrationForm()

    return render(request, 'accounts/owner_register.html', {'form': form, 'title': 'Register as Turf Owner'})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('home')


@login_required
@customer_required
def customer_profile_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('customer_profile')
        else:
            messages.error(request, "Please check the input values.")
    else:
        initial = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        }
        form = CustomerProfileForm(instance=profile, initial=initial)

    context = {
        'form': form,
        'title': 'My Profile'
    }
    return render(request, 'accounts/customer_profile.html', context)


@login_required
@owner_required
def owner_settings_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = OwnerSettingsForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Owner profile and UPI payment settings updated successfully!")
            return redirect('owner_settings')
        else:
            messages.error(request, "Error updating settings.")
    else:
        form = OwnerSettingsForm(instance=profile)

    context = {
        'form': form,
        'title': 'Turf Owner & UPI Settings'
    }
    return render(request, 'accounts/owner_settings.html', context)


def forgot_password_view(request):
    """
    Beginner-friendly and demo-ready password reset view.
    Allows testing password reset without complex external SMTP configuration.
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not email or not new_password:
            messages.error(request, "Please enter both email and new password.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        elif len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
        else:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                user.set_password(new_password)
                user.save()
                messages.success(request, f"Password successfully reset for {user.username}! You can now log in.")
                return redirect('customer_login')
            else:
                messages.error(request, f"No account found associated with {email}.")

    return render(request, 'accounts/forgot_password.html', {'title': 'Reset Password'})

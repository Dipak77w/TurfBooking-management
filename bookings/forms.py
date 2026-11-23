from django import forms
from .models import Booking, Payment


class BookingForm(forms.ModelForm):
    sport = forms.CharField(
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True})
    )
    start_time = forms.TimeField(
        widget=forms.HiddenInput()
    )
    end_time = forms.TimeField(
        widget=forms.HiddenInput()
    )
    player_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name of team captain / player', 'required': True})
    )
    player_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210', 'required': True})
    )
    player_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'captain@example.com (optional for confirmation)'})
    )
    special_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any special requests (e.g. need extra football, bibs, cricket bats)...'})
    )

    class Meta:
        model = Booking
        fields = [
            'sport', 'booking_date', 'start_time', 'end_time', 
            'player_name', 'player_phone', 'player_email', 'special_notes'
        ]


class PaymentSubmissionForm(forms.ModelForm):
    upi_reference_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control font-monospace', 
            'placeholder': 'Enter 12-digit UPI UTR / Transaction ID (e.g. 432189012345)',
            'required': True
        })
    )
    payment_screenshot = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Payment
        fields = ['upi_reference_id', 'payment_screenshot']

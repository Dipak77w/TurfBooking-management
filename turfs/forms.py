from django import forms
from .models import Turf, TurfImage, BlockedSlot, Review


class TurfForm(forms.ModelForm):
    class Meta:
        model = Turf
        fields = [
            'name', 'area', 'city', 'address', 'google_maps_url',
            'turf_type', 'size', 'available_sports', 'hourly_price',
            'opening_time', 'closing_time', 'slot_duration_minutes',
            'facilities', 'contact_number', 'description', 
            'rules_and_regulations', 'featured_image', 'is_demo'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. City Sports Arena'}),
            'area': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CIDCO Cannaught Place'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Chhatrapati Sambhajinagar'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Complete street address'}),
            'google_maps_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Google Maps URL or embed link'}),
            'turf_type': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 110 x 65 ft'}),
            'available_sports': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Football, Box Cricket, Badminton'}),
            'hourly_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '800.00', 'step': '50'}),
            'opening_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'slot_duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'value': '60'}),
            'facilities': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Floodlights, Parking, Drinking Water, Washroom'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+91 98765 43210'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed description of the turf...'}),
            'rules_and_regulations': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'featured_image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_demo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TurfImageForm(forms.ModelForm):
    class Meta:
        model = TurfImage
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control', 'required': True}),
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Floodlit Night View'}),
        }


class BlockedSlotForm(forms.ModelForm):
    class Meta:
        model = BlockedSlot
        fields = ['block_date', 'start_time', 'end_time', 'reason']
        widgets = {
            'block_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Turf Grass Renovation / Private Tournament'}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}, choices=[
                (5, '⭐⭐⭐⭐⭐ (5/5 Excellent)'),
                (4, '⭐⭐⭐⭐ (4/5 Very Good)'),
                (3, '⭐⭐⭐ (3/5 Good)'),
                (2, '⭐⭐ (2/5 Fair)'),
                (1, '⭐ (1/5 Poor)'),
            ]),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share your match experience, turf quality, lighting, and amenities...'}),
        }

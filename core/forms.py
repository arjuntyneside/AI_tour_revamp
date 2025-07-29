from django import forms
from .models import Departure, Customer, CustomerNote, Tour

class DepartureForm(forms.ModelForm):
    class Meta:
        model = Departure
        fields = ['title', 'country', 'duration_days', 'departure_date', 'group_size_current', 'group_size_max', 'price_gbp']

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['initials', 'full_name', 'email', 'phone_number', 'location', 'bookings_count', 'last_interaction_date']

class CustomerNoteForm(forms.ModelForm):
    class Meta:
        model = CustomerNote
        fields = ['note_text']
        widgets = {
            'note_text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter your note here...'})
        }

class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = ['title', 'destination', 'duration_days', 'price_gbp', 'description', 'highlights', 'included_services', 'excluded_services', 'max_group_size', 'difficulty_level', 'image', 'image_url']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Detailed tour description...'}),
            'highlights': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Key highlights of the tour...'}),
            'included_services': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What\'s included in the tour...'}),
            'excluded_services': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What\'s not included (optional)...'}),
        } 
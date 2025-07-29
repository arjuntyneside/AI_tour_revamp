from django import forms
from .models import Departure, Customer, CustomerNote, Tour

class DepartureForm(forms.ModelForm):
    class Meta:
        model = Departure
        fields = [
            'title', 'country', 'duration_days', 'departure_date', 
            'group_size_current', 'group_size_max', 'pricing_type', 
            'price_per_person', 'price_per_group'
        ]
        widgets = {
            'price_per_person': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'price_per_group': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'title': 'Total price for the entire group'}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'initials', 'full_name', 'email', 'phone_number', 'location', 
            'bookings_count', 'last_interaction_date', 'total_spent', 
            'cancellation_rate', 'customer_segment'
        ]
        widgets = {
            'total_spent': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cancellation_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
        }

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
        fields = [
            'title', 'destination', 'duration_days', 'pricing_type',
            'price_per_person', 'price_per_group', 'description', 
            'highlights', 'included_services', 'excluded_services', 'max_group_size', 
            'difficulty_level', 'image', 'image_url', 'cost_per_person', 'operational_costs', 
            'profit_margin_percentage', 'seasonal_demand'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Detailed tour description...'}),
            'highlights': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Key highlights of the tour...'}),
            'included_services': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What\'s included in the tour...'}),
            'excluded_services': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What\'s not included (optional)...'}),
            'price_per_person': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'price_per_group': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'title': 'Total price for the entire group'}),
            'cost_per_person': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'operational_costs': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'profit_margin_percentage': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
        } 
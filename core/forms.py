from django import forms
from .models import (
    Customer, CustomerNote, Tour, TourDeparture, TourOperator, 
    TourOperatorUser, DocumentUpload, Booking
)

class TourOperatorForm(forms.ModelForm):
    class Meta:
        model = TourOperator
        fields = [
            'name', 'company_name', 'email', 'phone', 'website', 'address',
            'subscription_plan', 'subscription_status', 'subscription_end_date',
            'ai_document_processing', 'ai_pricing_analysis', 
            'ai_demand_forecasting', 'ai_customer_segmentation'
        ]
        widgets = {
            'subscription_end_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = DocumentUpload
        fields = ['file_name', 'file_type']
        widgets = {
            'file_name': forms.TextInput(attrs={'placeholder': 'Enter file name...'}),
        }

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'initials', 'full_name', 'email', 'phone_number', 'location', 
            'ai_customer_segment', 'total_spent', 'bookings_count', 
            'cancellation_rate', 'last_interaction_date'
        ]
        widgets = {
            'total_spent': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'cancellation_rate': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '100'}),
            'last_interaction_date': forms.DateInput(attrs={'type': 'date'}),
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
            'difficulty_level', 'cost_per_person', 'operational_costs', 
            'profit_margin_percentage', 'seasonal_demand', 'status'
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

class TourDepartureForm(forms.ModelForm):
    class Meta:
        model = TourDeparture
        fields = [
            'departure_date', 'total_bookings', 'status',
            'fixed_costs', 'variable_costs_per_person', 'marketing_costs', 'commission_rate',
            'current_price_per_person', 'discounted_price_per_person'
        ]
        widgets = {
            'departure_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'total_bookings': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'fixed_costs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'variable_costs_per_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'marketing_costs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'max': '100'}),
            'current_price_per_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'discounted_price_per_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tour = kwargs.pop('tour', None)
        super().__init__(*args, **kwargs)
        
        # Set default values from tour if provided
        if self.tour:
            if not self.instance.pk:  # Only for new departures
                self.fields['current_price_per_person'].initial = self.tour.price_per_person
                self.fields['variable_costs_per_person'].initial = self.tour.cost_per_person

class TourDepartureFormWithTour(forms.ModelForm):
    """Form for creating departures when tour is not pre-selected"""
    class Meta:
        model = TourDeparture
        fields = [
            'tour', 'departure_date', 'total_bookings', 'status',
            'fixed_costs', 'variable_costs_per_person', 'marketing_costs', 'commission_rate',
            'current_price_per_person', 'discounted_price_per_person'
        ]
        widgets = {
            'tour': forms.Select(attrs={'class': 'form-control'}),
            'departure_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'total_bookings': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': '0'}),
            'fixed_costs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'variable_costs_per_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'marketing_costs': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00', 'max': '100'}),
            'current_price_per_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'discounted_price_per_person': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
        }
    
    def __init__(self, *args, **kwargs):
        tour_operator = kwargs.pop('tour_operator', None)
        super().__init__(*args, **kwargs)
        if tour_operator:
            self.fields['tour'].queryset = Tour.objects.filter(tour_operator=tour_operator)

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'tour', 'departure', 'customer', 'number_of_people', 
            'total_amount', 'status', 'notes'
        ]
        widgets = {
            'total_amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional notes...'}),
        } 
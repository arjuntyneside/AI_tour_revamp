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
    # Add a search field for customers
    customer_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search customers by name...',
            'id': 'customer-search'
        }),
        help_text="Type to search for customers"
    )
    
    class Meta:
        model = Booking
        fields = [
            'tour', 'departure', 'customer', 'customer_search', 'number_of_people', 
            'total_amount', 'status', 'notes'
        ]
        widgets = {
            'tour': forms.HiddenInput(),
            'departure': forms.HiddenInput(),
            'customer': forms.Select(attrs={'class': 'form-control', 'id': 'customer-select'}),
            'number_of_people': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '20'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'readonly': True}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes, special requirements, dietary needs...'}),
        }
    
    def __init__(self, *args, **kwargs):
        tour_operator = kwargs.pop('tour_operator', None)
        super().__init__(*args, **kwargs)
        
        # Store tour_operator for validation
        self._tour_operator = tour_operator
        
        if tour_operator:
            # Load all customers - much simpler and more reliable
            customers = Customer.objects.filter(
                tour_operator=tour_operator
            ).only('id', 'full_name', 'initials', 'email').distinct().order_by('full_name')
            self.fields['customer'].queryset = customers
        
        # Make total_amount readonly as it will be calculated automatically
        self.fields['total_amount'].widget.attrs['readonly'] = True
        
        # Override the customer field to show unique identifiers
        if 'customer' in self.fields:
            self.fields['customer'].label_from_instance = self._get_customer_display_name
    
    def _get_customer_display_name(self, customer):
        """Create a unique display name for customers to avoid confusion with duplicates"""
        # Use initials and email to make each customer unique
        if customer.initials and customer.email:
            return f"{customer.full_name} ({customer.initials}) - {customer.email}"
        elif customer.initials:
            return f"{customer.full_name} ({customer.initials})"
        elif customer.email:
            return f"{customer.full_name} - {customer.email}"
        else:
            return f"{customer.full_name} (ID: {customer.id})"
    
    def clean_customer(self):
        """Custom validation for customer field"""
        customer = self.cleaned_data.get('customer')
        if customer:
            # Check if customer exists and belongs to the tour operator
            tour_operator = getattr(self, '_tour_operator', None)
            if tour_operator:
                try:
                    # Verify the customer exists and belongs to the tour operator
                    valid_customer = Customer.objects.get(id=customer.id, tour_operator=tour_operator)
                    return valid_customer
                except Customer.DoesNotExist:
                    raise forms.ValidationError("Selected customer is not valid for this tour operator.")
        return customer
    
    def refresh_customer_queryset(self):
        """Refresh the customer queryset - useful after data changes"""
        if hasattr(self, '_tour_operator') and self._tour_operator:
            customers = Customer.objects.filter(
                tour_operator=self._tour_operator
            ).only('id', 'full_name', 'initials', 'email').distinct().order_by('full_name')
            self.fields['customer'].queryset = customers 
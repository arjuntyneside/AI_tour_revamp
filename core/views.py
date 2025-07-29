from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Departure, Customer, CustomerNote, Tour
from .forms import DepartureForm, CustomerForm, CustomerNoteForm, TourForm
import pandas as pd
import io
from django.shortcuts import get_object_or_404

def process_customer_import(uploaded_file):
    """Process uploaded CSV/Excel file and return list of customers to create"""
    customers_to_create = []
    errors = []
    
    try:
        # Determine file type and read accordingly
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(uploaded_file)
        else:
            return [], ["Unsupported file format. Please upload CSV or Excel files."]
        
        # Expected columns
        expected_columns = ['initials', 'full_name', 'email', 'phone_number', 'location', 'bookings_count', 'last_interaction_date']
        
        # Check if required columns exist
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            return [], [f"Missing required columns: {', '.join(missing_columns)}"]
        
        for index, row in df.iterrows():
            try:
                # Handle NaN values
                phone_number = row['phone_number'] if pd.notna(row['phone_number']) else None
                location = row['location'] if pd.notna(row['location']) else None
                bookings_count = int(row['bookings_count']) if pd.notna(row['bookings_count']) else 0
                last_interaction = row['last_interaction_date'] if pd.notna(row['last_interaction_date']) else None
                
                # Convert date string to date object if needed
                if last_interaction and isinstance(last_interaction, str):
                    try:
                        last_interaction = pd.to_datetime(last_interaction).date()
                    except:
                        last_interaction = None
                
                customer_data = {
                    'initials': str(row['initials']).strip(),
                    'full_name': str(row['full_name']).strip(),
                    'email': str(row['email']).strip(),
                    'phone_number': phone_number,
                    'location': location,
                    'bookings_count': bookings_count,
                    'last_interaction_date': last_interaction
                }
                
                # Validate email format
                if not customer_data['email'] or '@' not in customer_data['email']:
                    errors.append(f"Row {index + 2}: Invalid email format")
                    continue
                
                customers_to_create.append(customer_data)
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")
    
    return customers_to_create, errors

@login_required
def dashboard(request):
    departures = Departure.objects.all().order_by('departure_date')
    return render(request, 'core/dashboard.html', {'departures': departures})

@login_required
def tours(request):
    if request.method == 'POST':
        form = TourForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Tour created successfully!")
            return redirect('tours')
    else:
        form = TourForm()
    
    # Get all tours
    tours_list = Tour.objects.all()
    
    return render(request, 'core/tours.html', {
        'form': form,
        'tours': tours_list
    })

@login_required
def tour_detail(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    
    return render(request, 'core/tour_detail.html', {
        'tour': tour
    })

@login_required
def customers(request):
    if request.method == 'POST':
        if 'import_file' in request.FILES:
            # Handle file import
            uploaded_file = request.FILES['import_file']
            
            customers_to_create, errors = process_customer_import(uploaded_file)
            
            if errors:
                for error in errors:
                    messages.error(request, error)
            else:
                # Create customers in bulk
                created_count = 0
                for customer_data in customers_to_create:
                    try:
                        Customer.objects.create(**customer_data)
                        created_count += 1
                    except Exception as e:
                        messages.error(request, f"Error creating customer {customer_data['full_name']}: {str(e)}")
                
                if created_count > 0:
                    messages.success(request, f"Successfully imported {created_count} customers!")
            
            return redirect('customers')
        else:
            # Handle regular form submission
            form = CustomerForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Customer added successfully!")
                return redirect('customers')
    else:
        form = CustomerForm()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        customers_list = Customer.objects.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(initials__icontains=search_query)
        ).order_by('full_name')
    else:
        customers_list = Customer.objects.all().order_by('full_name')
    
    return render(request, 'core/customers.html', {
        'form': form, 
        'customers': customers_list,
        'search_query': search_query
    })

@login_required
def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    
    if request.method == 'POST':
        note_form = CustomerNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.customer = customer
            note.created_by = request.user
            note.save()
            messages.success(request, "Note added successfully!")
            return redirect('customer_detail', customer_id=customer.id)
    else:
        note_form = CustomerNoteForm()
    
    # Get all notes for this customer
    notes = customer.notes.all()
    
    return render(request, 'core/customer_detail.html', {
        'customer': customer,
        'notes': notes,
        'note_form': note_form
    })

@login_required
def settings(request):
    return render(request, 'core/settings.html')

@login_required
def departures(request):
    if request.method == 'POST':
        form = DepartureForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('departures')
    else:
        form = DepartureForm()
    all_departures = Departure.objects.all().order_by('departure_date')
    return render(request, 'core/departures.html', {'form': form, 'departures': all_departures})

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'core/login.html')

def logout(request):
    auth_logout(request)
    return redirect('login')
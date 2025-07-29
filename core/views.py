from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Customer, CustomerNote, Tour, TourDeparture
from .forms import CustomerForm, CustomerNoteForm, TourForm
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
    departures = TourDeparture.objects.all().order_by('departure_date')
    total_customers = Customer.objects.count()
    total_tours = Tour.objects.count()
    profitable_tours = Tour.objects.all()[:5]
    loss_making_tours = []
    for tour in Tour.objects.all():
        tour_departures = TourDeparture.objects.filter(tour=tour)
        if not tour_departures.exists():
            loss_making_tours.append(tour)
        # No occupancy logic since group size is not tracked
    loss_making_tours = loss_making_tours[:5]
    # No occupancy or revenue logic since group size is not tracked
    dashboard_data = {
        'departures': departures,
        'total_revenue': 0,
        'total_customers': total_customers,
        'total_tours': total_tours,
        'profitable_tours': profitable_tours,
        'loss_making_tours': loss_making_tours,
        'occupancy_rate': 0,
        'customer_engagement_rate': 0,
        'total_booked': 0,
        'total_capacity': 0,
        'display_name': request.user.get_full_name(),
    }
    return render(request, 'core/dashboard.html', dashboard_data)

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

    # Get all tours and annotate with departures info
    tours_list = []
    for tour in Tour.objects.all():
        departures = tour.departures.order_by('departure_date')
        departures_count = departures.count()
        next_departure = departures.first().departure_date if departures.exists() else None
        tour.departures_count = departures_count
        tour.next_departure = next_departure
        tours_list.append(tour)

    return render(request, 'core/tours.html', {
        'form': form,
        'tours': tours_list
    })

@login_required
def tour_detail(request, tour_id):
    tour = get_object_or_404(Tour, id=tour_id)
    tour_departures = TourDeparture.objects.filter(tour=tour).order_by('departure_date')

    # Handle add/delete departure date
    if request.method == 'POST':
        if 'add_departure' in request.POST:
            date_str = request.POST.get('departure_date')
            if date_str:
                try:
                    from datetime import datetime
                    dep_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    TourDeparture.objects.create(tour=tour, departure_date=dep_date)
                    messages.success(request, 'Departure date added!')
                except Exception as e:
                    messages.error(request, f'Invalid date: {e}')
            return redirect('tour_detail', tour_id=tour.id)
        elif 'delete_departure' in request.POST:
            dep_id = request.POST.get('delete_departure')
            TourDeparture.objects.filter(id=dep_id, tour=tour).delete()
            messages.success(request, 'Departure date deleted!')
            return redirect('tour_detail', tour_id=tour.id)

    profitability_data = {
        'total_revenue': 0,
        'total_travelers': 0,
        'total_tour_cost': 0,
        'operational_costs': tour.operational_costs,
        'net_profit': 0,
        'profit_margin': 0,
        'break_even_travelers': 0,
        'occupancy_rate': 0,
        'total_capacity': 0,
        'cost_per_person': tour.cost_per_person,
        'price_per_person': tour.effective_price_per_person,
    }
    return render(request, 'core/tour_detail.html', {
        'tour': tour,
        'profitability': profitability_data,
        'departures': tour_departures,
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
def departures(request):
    from datetime import date
    departures = TourDeparture.objects.select_related('tour').order_by('departure_date')
    today = date.today()
    for dep in departures:
        dep.days_left = (dep.departure_date - today).days
    return render(request, 'core/departures.html', {'departures': departures})

@login_required
def settings(request):
    user = request.user
    if request.method == 'POST':
        new_name = request.POST.get('name', '').strip()
        new_email = request.POST.get('email', '').strip()
        changed = False
        if new_name and (new_name != user.get_full_name()):
            # Split name into first and last (simple logic)
            name_parts = new_name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            changed = True
        if new_email and (new_email != user.email):
            user.email = new_email
            changed = True
        if changed:
            user.save()
            messages.success(request, 'Profile updated successfully!')
        else:
            messages.info(request, 'No changes made.')
        return redirect('settings')
    return render(request, 'core/settings.html', {'user': user})

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
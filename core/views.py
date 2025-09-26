from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, Avg
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings as django_settings
from datetime import datetime, timedelta
from django import forms
import json
import uuid
import os
import csv
import pandas as pd
from io import StringIO

from .models import (
    TourOperator, TourOperatorUser, DocumentUpload, AIProcessingJob,
    Tour, TourDeparture, Customer, Booking, CustomerNote, AIAnalytics
)
from .forms import (
    TourOperatorForm, DocumentUploadForm,
    CustomerForm, CustomerNoteForm, TourForm, TourDepartureForm, BookingForm
)

# Login form
class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

# Helper function to get current user's tour operator
def get_user_tour_operator(user):
    """Get the tour operator associated with the current user"""
    try:
        tour_operator_user = TourOperatorUser.objects.get(user=user, is_active=True)
        return tour_operator_user.tour_operator
    except TourOperatorUser.DoesNotExist:
        return None

# Multi-tenant middleware decorator
def require_tour_operator(view_func):
    """Decorator to ensure user has access to a tour operator"""
    def wrapper(request, *args, **kwargs):
        # Allow superusers to bypass tour operator requirement
        if request.user.is_superuser:
            # For superusers, try to get any tour operator or create a default one
            tour_operator = get_user_tour_operator(request.user)
            if not tour_operator:
                # Create a default tour operator for superusers
                from .models import TourOperator
                tour_operator, created = TourOperator.objects.get_or_create(
                    name="Default Tour Operator",
                    defaults={
                        'company_name': 'Default Tour Operator',
                        'email': request.user.email or 'admin@example.com',
                        'phone': '+1234567890',
                        'address': 'Default Address',
                        'website': 'https://example.com'
                    }
                )
                # Create TourOperatorUser association
                TourOperatorUser.objects.get_or_create(
                    user=request.user,
                    tour_operator=tour_operator,
                    defaults={'is_active': True}
                )
            request.tour_operator = tour_operator
            return view_func(request, *args, **kwargs)
        
        # For regular users, require tour operator access
        tour_operator = get_user_tour_operator(request.user)
        if not tour_operator:
            messages.error(request, "You don't have access to any tour operator account.")
            return redirect('login')
        request.tour_operator = tour_operator
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@require_tour_operator
def dashboard(request):
    """AI-powered dashboard with business intelligence"""
    tour_operator = request.tour_operator
    
    # Get all departures for analytics
    departures = TourDeparture.objects.filter(
        tour__tour_operator=tour_operator
    ).order_by('departure_date')
    
    # Calculate monthly trends (last 6 months)
    today = timezone.now().date()
    months_data = []
    revenue_data = []
    profit_data = []
    cost_data = []
    
    for i in range(6):
        month_date = today - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        if i == 0:
            month_end = today
        else:
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Get departures in this month
        month_departures = departures.filter(
            departure_date__gte=month_start,
            departure_date__lte=month_end
        )
        
        # Calculate metrics - Convert Decimal to float for JSON serialization
        month_revenue = float(sum(dep.current_revenue for dep in month_departures))
        month_profit = float(sum(dep.current_profit or 0 for dep in month_departures))
        month_costs = float(sum(
            dep.fixed_costs + dep.marketing_costs + (dep.variable_costs_per_person * dep.slots_filled)
            for dep in month_departures
        ))
        
        months_data.append(month_start.strftime('%b %Y'))
        revenue_data.append(month_revenue)
        profit_data.append(month_profit)
        cost_data.append(month_costs)
    
    # Reverse to show oldest to newest
    months_data.reverse()
    revenue_data.reverse()
    profit_data.reverse()
    cost_data.reverse()
    
    # Calculate overall metrics - Convert to float
    total_revenue = float(sum(revenue_data))
    total_profit = float(sum(profit_data))
    total_costs = float(sum(cost_data))
    total_departures = departures.count()
    profitable_departures = sum(1 for dep in departures if dep.is_profitable)
    
    # Calculate averages - Convert to float
    avg_revenue_per_departure = float(total_revenue / total_departures if total_departures > 0 else 0)
    avg_profit_per_departure = float(total_profit / total_departures if total_departures > 0 else 0)
    profit_margin = float((total_profit / total_revenue * 100) if total_revenue > 0 else 0)
    
    # Get top performing tours
    tour_performance = {}
    for dep in departures:
        tour_name = dep.tour.title
        if tour_name not in tour_performance:
            tour_performance[tour_name] = {
                'revenue': 0,
                'profit': 0,
                'departures': 0
            }
        tour_performance[tour_name]['revenue'] += float(dep.current_revenue)
        tour_performance[tour_name]['profit'] += float(dep.current_profit or 0)
        tour_performance[tour_name]['departures'] += 1
    
    # Sort by profit
    top_tours = sorted(
        [{'name': k, **v} for k, v in tour_performance.items()],
        key=lambda x: x['profit'],
        reverse=True
    )[:5]
    
    # Calculate percentage for progress bars
    if top_tours:
        max_profit = top_tours[0]['profit']
        for tour in top_tours:
            tour['percentage'] = float((tour['profit'] / max_profit * 100) if max_profit > 0 else 0)
    
    # Risk alerts (unprofitable departures)
    risk_departures = [
        dep for dep in departures.filter(departure_date__gte=today)
        if not dep.is_profitable and dep.slots_filled > 0
    ][:3]
    
    import json
    
    context = {
        'tour_operator': tour_operator,
        'months_data': json.dumps(months_data, ensure_ascii=False),
        'revenue_data': json.dumps(revenue_data, ensure_ascii=False),
        'profit_data': json.dumps(profit_data, ensure_ascii=False),
        'cost_data': json.dumps(cost_data, ensure_ascii=False),
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'total_costs': total_costs,
        'total_departures': total_departures,
        'profitable_departures': profitable_departures,
        'avg_revenue_per_departure': avg_revenue_per_departure,
        'avg_profit_per_departure': avg_profit_per_departure,
        'profit_margin': profit_margin,
        'top_tours': top_tours,
        'risk_departures': risk_departures,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
@require_tour_operator
def document_upload(request):
    """AI document processing interface"""
    tour_operator = request.tour_operator
    
    if request.method == 'POST':
        uploaded_file = request.FILES.get('document')
        file_name = request.POST.get('file_name', '')
        
        if uploaded_file:
            # Validate file size (10MB limit)
            if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
                messages.error(request, "File size must be less than 10MB.")
                return redirect('document_upload')
            
            # Validate file type
            allowed_types = ['.pdf', '.docx', '.xlsx', '.xls', '.txt']
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            if file_extension not in allowed_types:
                messages.error(request, f"File type {file_extension} is not supported. Please upload PDF, DOCX, Excel, or TXT files.")
                return redirect('document_upload')
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(django_settings.BASE_DIR, 'uploads', 'documents', str(tour_operator.id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save the file
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # Create document record
            document = DocumentUpload.objects.create(
                tour_operator=tour_operator,
                uploaded_by=request.user,
                file_name=file_name or uploaded_file.name,
                file_size=uploaded_file.size,
                file_type=file_extension[1:].upper(),
                file_path=file_path,
                processing_status='pending'
            )
            

            
            messages.success(request, f"Document '{document.file_name}' uploaded successfully! You can now process it with AI.")
            return redirect('document_processing')
        else:
            messages.error(request, "Please select a file to upload.")
    
    # Get recent documents
    recent_documents = DocumentUpload.objects.filter(
        tour_operator=tour_operator
    ).order_by('-uploaded_date')[:10]
    
    context = {
        'recent_documents': recent_documents,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/document_upload.html', context)

@login_required
@require_tour_operator
def document_processing(request):
    """Document processing status and results"""
    tour_operator = request.tour_operator
    
    documents = DocumentUpload.objects.filter(
        tour_operator=tour_operator
    ).order_by('-uploaded_date')
    
    # AI processing jobs
    processing_jobs = AIProcessingJob.objects.filter(
        document__tour_operator=tour_operator
    ).order_by('-created_date')
    
    context = {
        'documents': documents,
        'processing_jobs': processing_jobs,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/document_processing.html', context)

@login_required
@require_tour_operator
def document_results(request, document_id):
    """View detailed results of document processing"""
    tour_operator = request.tour_operator
    document = get_object_or_404(DocumentUpload, id=document_id, tour_operator=tour_operator)
    
    # Get tours created from this document
    extracted_tours = Tour.objects.filter(source_document=document)
    
    # Get AI processing jobs for this document
    ai_jobs = AIProcessingJob.objects.filter(document=document)
    
    context = {
        'document': document,
        'extracted_tours': extracted_tours,
        'ai_jobs': ai_jobs,
    }
    
    return render(request, 'core/document_results.html', context)

@login_required
@require_tour_operator
def create_tour_from_document(request, document_id):
    """Create a new tour from processed document data"""
    tour_operator = request.tour_operator
    document = get_object_or_404(DocumentUpload, id=document_id, tour_operator=tour_operator)
    
    if request.method == 'POST':
        # Handle tour creation from form
        form = TourForm(request.POST)
        if form.is_valid():
            tour = form.save(commit=False)
            tour.tour_operator = tour_operator
            tour.source_document = document
            tour.save()
            
            messages.success(request, f"Tour '{tour.title}' created successfully!")
            return redirect('tour_detail', tour_id=tour.id)
    else:
        # Pre-populate form with extracted data
        extracted_data = document.extracted_data
        if extracted_data and 'extracted_tours' in extracted_data:
            tour_data = extracted_data['extracted_tours'][0] if extracted_data['extracted_tours'] else {}
            initial_data = {
                'title': tour_data.get('title', ''),
                'destination': tour_data.get('destination', ''),
                'duration_days': tour_data.get('duration_days', 1),
                'max_group_size': tour_data.get('max_group_size', 15),
                'pricing_type': tour_data.get('pricing_type', 'per_person'),
                'price_per_person': tour_data.get('price_per_person', 0),
                'description': tour_data.get('description', ''),
                'highlights': tour_data.get('highlights', ''),
                'included_services': tour_data.get('included_services', ''),
                'excluded_services': tour_data.get('excluded_services', ''),
                'difficulty_level': tour_data.get('difficulty_level', 'moderate'),
                'seasonal_demand': tour_data.get('seasonal_demand', 'medium'),
            }
            form = TourForm(initial=initial_data)
        else:
            form = TourForm()
    
    context = {
        'form': form,
        'document': document,
        'extracted_data': document.extracted_data,
    }
    
    return render(request, 'core/create_tour_from_document.html', context)

@login_required
@require_tour_operator
def retry_document_processing(request, document_id):
    """Retry processing a failed document"""
    tour_operator = request.tour_operator
    document = get_object_or_404(DocumentUpload, id=document_id, tour_operator=tour_operator)
    
    # Reset document status
    document.processing_status = 'pending'
    document.processing_errors = ''
    document.save()
    
    # Create new AI processing job
    ai_job = AIProcessingJob.objects.create(
        document=document,
        job_type='document_extraction',
        status='queued'
    )
    
    # Process immediately
    try:
        from core.management.commands.process_ai_jobs import Command
        processor = Command()
        processor.process_single_job(ai_job)
        messages.success(request, f"Document '{document.file_name}' reprocessed successfully!")
    except Exception as e:
        messages.error(request, f"Reprocessing failed: {str(e)}")
    
    return redirect('document_processing')

@login_required
@require_tour_operator
def process_document(request, document_id):
    """Process a document with AI"""
    tour_operator = request.tour_operator
    document = get_object_or_404(DocumentUpload, id=document_id, tour_operator=tour_operator)
    
    # Update document status to processing
    document.processing_status = 'processing'
    document.save()
    
    # Create AI processing job
    ai_job = AIProcessingJob.objects.create(
        document=document,
        job_type='document_extraction',
        status='processing'
    )
    
    try:
        from core.management.commands.process_ai_jobs import Command
        processor = Command()
        
        # Initialize AI processor
        from django.conf import settings
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        if not api_key:
            messages.error(request, "AI processing failed: No API key found.")
            document.processing_status = 'failed'
            document.save()
            return redirect('document_processing')
        
        from core.gemini_ai_processing import GeminiAIProcessor
        ai_processor = GeminiAIProcessor(api_key)
        
        # Process the job with proper AI processor
        result = processor.process_with_gemini(document, ai_processor)
        
        # Update document with results
        document.extracted_data = result
        document.confidence_score = result.get('extraction_confidence', 0) * 100
        document.processing_status = 'completed'
        document.processed_date = timezone.now()
        document.save()
        
        # Create tours from extraction
        processor.create_tours_from_extraction(document, result)
        
        # Update AI job status
        ai_job.status = 'completed'
        ai_job.save()
        
        messages.success(request, f"Document '{document.file_name}' processed successfully with {document.confidence_score}% confidence!")
        
    except Exception as e:
        import traceback
        error_msg = f"Processing failed: {str(e)}"
        print(f"ERROR in process_document: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        
        messages.error(request, error_msg)
        document.processing_status = 'failed'
        document.processing_errors = str(e)
        document.save()
        
        # Update AI job status
        ai_job.status = 'failed'
        ai_job.error_message = str(e)
        ai_job.save()
    
    return redirect('document_processing')

@login_required
@require_tour_operator
def delete_document(request, document_id):
    """Delete a document and its associated data"""
    tour_operator = request.tour_operator
    document = get_object_or_404(DocumentUpload, id=document_id, tour_operator=tour_operator)
    
    # Delete associated tours
    tours_to_delete = Tour.objects.filter(source_document=document)
    tours_count = tours_to_delete.count()
    tours_to_delete.delete()
    
    # Delete the file from disk
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        messages.warning(request, f"File could not be deleted from disk: {str(e)}")
    
    # Delete the document
    document_name = document.file_name
    document.delete()
    
    messages.success(request, f"Document '{document_name}' and {tours_count} associated tours deleted successfully!")
    return redirect('document_processing')

@login_required
@require_tour_operator
def stop_processing(request, document_id):
    """Stop processing a document"""
    tour_operator = request.tour_operator
    document = get_object_or_404(DocumentUpload, id=document_id, tour_operator=tour_operator)
    
    # Cancel any pending AI jobs
    pending_jobs = AIProcessingJob.objects.filter(
        document=document,
        status__in=['queued', 'processing']
    )
    for job in pending_jobs:
        job.status = 'failed'
        job.error_message = 'Processing cancelled by user'
        job.save()
    
    # Update document status
    document.processing_status = 'failed'
    document.processing_errors = 'Processing cancelled by user'
    document.save()
    
    messages.success(request, f"Processing stopped for document '{document.file_name}'")
    return redirect('document_processing')

@login_required
@require_tour_operator
def processing_status(request, document_id):
    """Get real-time processing status for a document"""
    tour_operator = request.tour_operator
    document = get_object_or_404(DocumentUpload, id=document_id, tour_operator=tour_operator)
    
    # Get the latest AI job for this document
    latest_job = AIProcessingJob.objects.filter(document=document).order_by('-created_date').first()
    
    status_data = {
        'document_id': str(document.id),
        'status': document.processing_status,
        'confidence_score': document.confidence_score,
        'processing_errors': document.processing_errors,
        'job_status': latest_job.status if latest_job else None,
        'job_error': latest_job.error_message if latest_job else None,
        'is_processing': document.processing_status == 'processing',
        'is_completed': document.processing_status == 'completed',
        'is_failed': document.processing_status == 'failed',
    }
    
    return JsonResponse(status_data)

@login_required
@require_tour_operator
def tours(request):
    """Tour management with AI insights"""
    tour_operator = request.tour_operator
    
    tours = Tour.objects.filter(tour_operator=tour_operator).order_by('-created_date')
    
    # Filter options
    status_filter = request.GET.get('status', '')
    if status_filter:
        tours = tours.filter(status=status_filter)
    
    # Add departure counts and next departure info
    for tour in tours:
        tour.departures_count = tour.departures.count()
        next_departure = tour.departures.filter(
            departure_date__gte=timezone.now().date()
        ).order_by('departure_date').first()
        tour.next_departure = next_departure.departure_date if next_departure else None
    
    context = {
        'tours': tours,
        'tour_operator': tour_operator,
        'status_filter': status_filter,
    }
    
    return render(request, 'core/tours.html', context)

@login_required
@require_tour_operator
def tour_detail(request, tour_id):
    """Tour detail with AI insights"""
    tour_operator = request.tour_operator
    tour = get_object_or_404(Tour, id=tour_id, tour_operator=tour_operator)
    
    # Get departures
    departures = TourDeparture.objects.filter(tour=tour).order_by('departure_date')
    
    # Get bookings
    bookings = Booking.objects.filter(tour=tour).order_by('-booking_date')
    
    # AI insights
    ai_analytics = AIAnalytics.objects.filter(
        tour_operator=tour_operator,
        analytics_type='demand_analysis'
    ).first()
    
    context = {
        'tour': tour,
        'departures': departures,
        'bookings': bookings,
        'ai_analytics': ai_analytics,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/tour_detail.html', context)

@login_required
@require_tour_operator
def edit_tour(request, tour_id):
    """Edit tour details"""
    tour_operator = request.tour_operator
    tour = get_object_or_404(Tour, id=tour_id, tour_operator=tour_operator)
    
    if request.method == 'POST':
        form = TourForm(request.POST, instance=tour)
        if form.is_valid():
            form.save()
            messages.success(request, "Tour updated successfully.")
            return redirect('tour_detail', tour_id=tour.id)
    else:
        form = TourForm(instance=tour)
    
    context = {
        'form': form,
        'tour': tour,
        'tour_operator': tour_operator,
        'action': 'Edit'
    }
    
    return render(request, 'core/tour_form.html', context)

@login_required
@require_tour_operator
def delete_tour(request, tour_id):
    """Delete tour with confirmation"""
    tour_operator = request.tour_operator
    tour = get_object_or_404(Tour, id=tour_id, tour_operator=tour_operator)
    
    if request.method == 'POST':
        # Check if tour has departures
        departures_count = tour.departures.count()
        if departures_count > 0:
            messages.error(request, f"Cannot delete tour '{tour.title}'. It has {departures_count} departure(s). Please delete all departures first.")
            return redirect('tour_detail', tour_id=tour.id)
        
        # Check if tour has bookings
        bookings_count = Booking.objects.filter(tour=tour).count()
        if bookings_count > 0:
            messages.error(request, f"Cannot delete tour '{tour.title}'. It has {bookings_count} booking(s). Please handle all bookings first.")
            return redirect('tour_detail', tour_id=tour.id)
        
        tour_title = tour.title
        tour.delete()
        messages.success(request, f"Tour '{tour_title}' has been deleted successfully.")
        return redirect('tours')
    
    context = {
        'tour': tour,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/delete_tour_confirm.html', context)

@login_required
@require_tour_operator
def customers(request):
    """Customer management with AI segmentation"""
    tour_operator = request.tour_operator
    
    customers = Customer.objects.filter(tour_operator=tour_operator).order_by('-created_date')
    
    # Filter by AI segment
    segment_filter = request.GET.get('segment', '')
    if segment_filter:
        customers = customers.filter(ai_customer_segment=segment_filter)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(initials__icontains=search_query)
        )
    
    # Initialize form
    form = CustomerForm()
    
    # Handle customer creation and import
    if request.method == 'POST':
        # Check if it's a file import
        if 'import_file' in request.FILES:
            import_file = request.FILES['import_file']
            
            try:
                # Handle CSV files
                if import_file.name.endswith('.csv'):
                    # Read CSV file
                    file_data = import_file.read().decode('utf-8')
                    csv_reader = csv.DictReader(StringIO(file_data))
                    
                    imported_count = 0
                    errors = []
                    
                    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 because row 1 is header
                        try:
                            # Create customer from CSV row
                            customer = Customer(
                                tour_operator=tour_operator,
                                initials=row.get('initials', ''),
                                full_name=row.get('full_name', ''),
                                email=row.get('email', ''),
                                phone_number=row.get('phone_number', '') or None,
                                location=row.get('location', '') or None,
                                ai_customer_segment=row.get('ai_customer_segment', 'new'),
                                total_spent=float(row.get('total_spent', 0)) if row.get('total_spent') else 0,
                                bookings_count=int(row.get('bookings_count', 0)) if row.get('bookings_count') else 0,
                                cancellation_rate=float(row.get('cancellation_rate', 0)) if row.get('cancellation_rate') else 0,
                                last_interaction_date=row.get('last_interaction_date') if row.get('last_interaction_date') else None
                            )
                            customer.save()
                            imported_count += 1
                            
                        except Exception as e:
                            errors.append(f"Row {row_num}: {str(e)}")
                    
                    if imported_count > 0:
                        messages.success(request, f"Successfully imported {imported_count} customers!")
                    if errors:
                        messages.warning(request, f"Some rows had errors: {'; '.join(errors[:5])}")
                        
                # Handle Excel files
                elif import_file.name.endswith(('.xlsx', '.xls')):
                    # Read Excel file
                    df = pd.read_excel(import_file)
                    
                    imported_count = 0
                    errors = []
                    
                    for index, row in df.iterrows():
                        try:
                            # Create customer from Excel row
                            customer = Customer(
                                tour_operator=tour_operator,
                                initials=str(row.get('initials', '')),
                                full_name=str(row.get('full_name', '')),
                                email=str(row.get('email', '')),
                                phone_number=str(row.get('phone_number', '')) if pd.notna(row.get('phone_number')) else None,
                                location=str(row.get('location', '')) if pd.notna(row.get('location')) else None,
                                ai_customer_segment=str(row.get('ai_customer_segment', 'new')),
                                total_spent=float(row.get('total_spent', 0)) if pd.notna(row.get('total_spent')) else 0,
                                bookings_count=int(row.get('bookings_count', 0)) if pd.notna(row.get('bookings_count')) else 0,
                                cancellation_rate=float(row.get('cancellation_rate', 0)) if pd.notna(row.get('cancellation_rate')) else 0,
                                last_interaction_date=row.get('last_interaction_date') if pd.notna(row.get('last_interaction_date')) else None
                            )
                            customer.save()
                            imported_count += 1
                            
                        except Exception as e:
                            errors.append(f"Row {index + 2}: {str(e)}")
                    
                    if imported_count > 0:
                        messages.success(request, f"Successfully imported {imported_count} customers!")
                    if errors:
                        messages.warning(request, f"Some rows had errors: {'; '.join(errors[:5])}")
                        
                else:
                    messages.error(request, "Please upload a CSV or Excel file (.csv, .xlsx, .xls)")
                    
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
                
        else:
            # Handle individual customer creation
            form = CustomerForm(request.POST)
            if form.is_valid():
                customer = form.save(commit=False)
                customer.tour_operator = tour_operator
                customer.save()
                messages.success(request, f"Customer {customer.full_name} added successfully!")
                return redirect('customers')
            else:
                messages.error(request, "Please correct the errors below.")
    
    context = {
        'customers': customers,
        'tour_operator': tour_operator,
        'segment_filter': segment_filter,
        'search_query': search_query,
        'form': form,
    }
    
    return render(request, 'core/customers.html', context)

@login_required
@require_tour_operator
def customer_detail(request, customer_id):
    """Customer detail with AI insights"""
    tour_operator = request.tour_operator
    customer = get_object_or_404(Customer, id=customer_id, tour_operator=tour_operator)
    
    # Get bookings
    bookings = Booking.objects.filter(customer=customer).order_by('-booking_date')
    
    # Get notes
    notes = CustomerNote.objects.filter(customer=customer).order_by('-created_date')
    
    if request.method == 'POST':
        note_form = CustomerNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.customer = customer
            note.created_by = request.user
            note.save()
            messages.success(request, "Note added successfully.")
            return redirect('customer_detail', customer_id=customer.id)
    else:
        note_form = CustomerNoteForm()
    
    context = {
        'customer': customer,
        'bookings': bookings,
        'notes': notes,
        'note_form': note_form,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/customer_detail.html', context)

@login_required
@require_tour_operator
def edit_customer(request, customer_id):
    """Edit customer information"""
    tour_operator = request.tour_operator
    customer = get_object_or_404(Customer, id=customer_id, tour_operator=tour_operator)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Customer {customer.full_name} updated successfully!")
            return redirect('customer_detail', customer_id=customer.id)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'customer': customer,
        'form': form,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/edit_customer.html', context)

@login_required
@require_tour_operator
def delete_customer(request, customer_id):
    """Delete customer"""
    tour_operator = request.tour_operator
    customer = get_object_or_404(Customer, id=customer_id, tour_operator=tour_operator)
    
    if request.method == 'POST':
        customer_name = customer.full_name
        customer.delete()
        messages.success(request, f"Customer {customer_name} deleted successfully!")
        return redirect('customers')
    
    context = {
        'customer': customer,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/delete_customer_confirm.html', context)

@login_required
@require_tour_operator
def bookings(request):
    """Booking management with AI insights"""
    tour_operator = request.tour_operator
    
    bookings = Booking.objects.filter(tour_operator=tour_operator).order_by('-booking_date')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'tour_operator': tour_operator,
        'status_filter': status_filter,
    }
    
    return render(request, 'core/bookings.html', context)

@login_required
@require_tour_operator
def departures(request):
    """View all departures with financial analysis"""
    tour_operator = request.tour_operator
    departures = TourDeparture.objects.filter(tour__tour_operator=tour_operator).order_by('departure_date')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        departures = departures.filter(status=status_filter)
    
    # Calculate overall financial metrics
    total_revenue = sum(departure.current_revenue for departure in departures)
    total_profit = sum(departure.current_profit or 0 for departure in departures)
    total_fixed_costs = sum(departure.fixed_costs for departure in departures)
    total_marketing_costs = sum(departure.marketing_costs for departure in departures)
    total_variable_costs = sum(departure.variable_costs_per_person * departure.slots_filled for departure in departures)
    total_commission = sum((departure.current_price_per_person * departure.commission_rate / 100) * departure.slots_filled for departure in departures)
    
    # Calculate average occupancy
    if departures:
        total_occupancy = sum(departure.current_occupancy_rate or 0 for departure in departures)
        avg_occupancy = total_occupancy / len(departures)
    else:
        avg_occupancy = 0
    
    # Count profitable departures
    profitable_count = sum(1 for departure in departures if departure.is_profitable)
    total_departures = len(departures)
    
    # Calculate overall ROI
    total_investment = total_fixed_costs + total_marketing_costs + total_variable_costs
    overall_roi = (total_profit / total_investment * 100) if total_investment > 0 else 0
    
    # Calculate total slots filled and capacity
    total_slots_filled = sum(departure.slots_filled for departure in departures)
    total_capacity = sum(departure.available_spots for departure in departures)
    overall_occupancy_rate = (total_slots_filled / total_capacity * 100) if total_capacity > 0 else 0
    
    # Add calculated fields to each departure for template use using breakeven analyzer
    from .breakeven_analysis import BreakevenAnalyzer
    
    for departure in departures:
        # Create breakeven analyzer for this departure
        analyzer = BreakevenAnalyzer(
            fixed_costs=departure.fixed_costs,
            variable_costs_per_person=departure.variable_costs_per_person,
            marketing_costs=departure.marketing_costs,
            price_per_person=departure.current_price_per_person,
            commission_rate=departure.commission_rate,
            max_capacity=departure.available_spots
        )
        
        # Get analysis results
        analysis = analyzer.get_breakeven_analysis(departure.slots_filled)
        cost_breakdown = analyzer.get_cost_breakdown(departure.slots_filled)
        
        # Update departure object with calculated fields
        departure.commission_amount = analysis['commission_amount_per_person'] * departure.slots_filled
        departure.net_revenue = departure.current_revenue - departure.commission_amount
        departure.remaining_spots = departure.available_spots - departure.slots_filled
        departure.total_costs = cost_breakdown['total_costs']
        departure.variable_costs_total = cost_breakdown['variable_costs_total']
        
        # Update breakeven fields if they're not set
        if not departure.breakeven_passengers:
            departure.breakeven_passengers = analysis['breakeven_passengers']
        if not departure.profit_at_capacity:
            departure.profit_at_capacity = analysis['profit_at_capacity']
        if not departure.roi_percentage:
            departure.roi_percentage = analysis['roi_percentage']
    
    # Get rule-based financial insights
    from .rule_based_financial_analysis import get_ai_financial_insights
    rule_based_insights = get_ai_financial_insights(tour_operator)
    
    context = {
        'departures': departures,
        'tour_operator': tour_operator,
        'status_filter': status_filter,
        'total_revenue': total_revenue,
        'total_profit': total_profit,
        'total_fixed_costs': total_fixed_costs,
        'total_marketing_costs': total_marketing_costs,
        'total_variable_costs': total_variable_costs,
        'total_commission': total_commission,
        'total_investment': total_investment,
        'overall_roi': overall_roi,
        'total_slots_filled': total_slots_filled,
        'total_capacity': total_capacity,
        'overall_occupancy_rate': overall_occupancy_rate,
        'avg_occupancy': avg_occupancy,
        'rule_based_insights': rule_based_insights,
        'profitable_count': profitable_count,
        'total_departures': total_departures,
    }
    
    return render(request, 'core/departures.html', context)


@login_required
@require_tour_operator
def ai_insights(request):
    """Display AI-powered financial insights"""
    tour_operator = request.tour_operator
    
    # Get both rule-based and AI insights
    from .rule_based_financial_analysis import get_ai_financial_insights
    from .gemini_ai_insights import get_gemini_ai_insights
    
    rule_based_insights = get_ai_financial_insights(tour_operator)
    gemini_ai_insights = get_gemini_ai_insights(tour_operator)
    
    context = {
        'tour_operator': tour_operator,
        'rule_based_insights': rule_based_insights,
        'gemini_ai_insights': gemini_ai_insights,
    }
    
    return render(request, 'core/ai_insights.html', context)

@login_required
@require_tour_operator
def ai_chat(request):
    """Handle AI chat requests"""
    if request.method == 'POST':
        import json
        from django.http import JsonResponse
        
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            
            if not user_message:
                return JsonResponse({'success': False, 'error': 'No message provided'})
            
            # Guardrails for allowed questions
            allowed_keywords = [
                'analyze', 'performance', 'profit', 'revenue', 'cost', 'pricing',
                'breakeven', 'departure', 'tour', 'financial', 'roi', 'occupancy',
                'booking', 'capacity', 'margin', 'optimization', 'strategy',
                'recommendation', 'improve', 'better', 'best', 'worst', 'compare'
            ]
            
            # Check if message contains allowed keywords
            message_lower = user_message.lower()
            has_allowed_keyword = any(keyword in message_lower for keyword in allowed_keywords)
            
            if not has_allowed_keyword:
                return JsonResponse({
                    'success': True,
                    'response': "I analyze tour financial performance. Ask about:\n\n- Profitability and revenue\n- Pricing strategies\n- Cost optimization\n- Breakeven analysis\n- Booking performance\n\nExamples: 'Analyze my tour financial performance' or 'Which departures are most profitable?'"
                })
            
            # Get tour operator data for AI analysis
            tour_operator = request.tour_operator
            from .gemini_ai_insights import GeminiAIFinancialInsights
            
            # Create AI analyzer
            ai_analyzer = GeminiAIFinancialInsights(tour_operator)
            
            # Prepare context for AI
            context_data = ai_analyzer._prepare_data_for_ai()
            
            # Create AI prompt
            ai_prompt = f"""
You are a business-focused AI assistant for a tour operator. The user asked: "{user_message}"

Based on this tour operator data, provide a CONCISE, business-focused response:

{json.dumps(context_data, indent=2)}

IMPORTANT GUIDELINES:
- Be direct and concise (max 3-4 paragraphs)
- Focus on actionable business insights
- Use plain text (no markdown, bold, stars, or formatting)
- Give specific numbers and percentages
- Provide 2-3 concrete action items
- Write for a busy business owner who wants quick insights

Focus on: profitability, pricing, demand, costs, and specific actions to improve business performance.
"""
            
            # Get AI response
            if ai_analyzer.model:
                try:
                    response = ai_analyzer.model.generate_content(ai_prompt)
                    ai_response = response.text.strip()
                    
                    # Clean up the response
                    if ai_response.startswith('```json'):
                        ai_response = ai_response.replace('```json', '').replace('```', '').strip()
                    
                    return JsonResponse({
                        'success': True,
                        'response': ai_response
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': True,
                        'response': f"Your tour performance summary:\n\nTotal revenue: ${context_data['summary_metrics'].get('total_revenue', 0):,.0f}\nTotal profit: ${context_data['summary_metrics'].get('total_profit', 0):,.0f}\nProfit margin: {context_data['summary_metrics'].get('overall_profit_margin', 0):.0f}%\nProfitable departures: {context_data['summary_metrics'].get('profitable_departures', 0)}/{context_data['summary_metrics'].get('total_departures', 0)}\n\nAsk specific questions about pricing, costs, or profitability for detailed insights."
                    })
            else:
                return JsonResponse({
                    'success': True,
                    'response': "I can analyze your tour financial performance. Ask me about profitability, pricing, costs, or specific departures for business insights."
                })
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@require_tour_operator
def create_departure(request):
    """Create a new departure with financial analysis"""
    tour_operator = request.tour_operator
    tour_id = request.GET.get('tour_id')
    
    if tour_id:
        # Create departure for specific tour
        tour = get_object_or_404(Tour, id=tour_id, tour_operator=tour_operator)
        
        if request.method == 'POST':
            form = TourDepartureForm(request.POST, tour=tour)
            if form.is_valid():
                departure = form.save(commit=False)
                departure.tour = tour
                departure.available_spots = tour.max_group_size  # Set from tour settings
                departure.save()
                messages.success(request, f"Departure for '{tour.title}' created successfully!")
                return redirect('departures')
        else:
            form = TourDepartureForm(tour=tour)
        
        context = {
            'form': form,
            'tour': tour,
            'tour_operator': tour_operator,
            'action': 'Create',
        }
    else:
        # Create departure with tour selection
        if request.method == 'POST':
            from .forms import TourDepartureFormWithTour
            form = TourDepartureFormWithTour(request.POST, tour_operator=tour_operator)
            if form.is_valid():
                departure = form.save(commit=False)
                departure.available_spots = departure.tour.max_group_size  # Set from tour settings
                departure.save()
                messages.success(request, f"Departure for '{departure.tour.title}' created successfully!")
                return redirect('departures')
        else:
            from .forms import TourDepartureFormWithTour
            form = TourDepartureFormWithTour(tour_operator=tour_operator)
        
        context = {
            'form': form,
            'tour_operator': tour_operator,
            'action': 'Create',
        }
    
    return render(request, 'core/departure_form.html', context)

@login_required
@require_tour_operator
def edit_departure(request, departure_id):
    """Edit a departure with financial analysis"""
    tour_operator = request.tour_operator
    departure = get_object_or_404(TourDeparture, id=departure_id, tour__tour_operator=tour_operator)
    
    if request.method == 'POST':
        form = TourDepartureForm(request.POST, instance=departure, tour=departure.tour)
        if form.is_valid():
            departure = form.save(commit=False)
            departure.available_spots = departure.tour.max_group_size  # Keep in sync with tour settings
            departure.save()
            messages.success(request, f"Departure for '{departure.tour.title}' updated successfully!")
            return redirect('departures')
    else:
        form = TourDepartureForm(instance=departure, tour=departure.tour)
    
    context = {
        'form': form,
        'departure': departure,
        'tour': departure.tour,
        'tour_operator': tour_operator,
        'action': 'Edit',
    }
    
    return render(request, 'core/departure_form.html', context)

@login_required
@require_tour_operator
def departure_detail(request, departure_id):
    """View detailed financial analysis for a departure"""
    tour_operator = request.tour_operator
    departure = get_object_or_404(TourDeparture, id=departure_id, tour__tour_operator=tour_operator)
    
    # Get bookings for this departure
    bookings = Booking.objects.filter(departure=departure).order_by('booking_date')
    
    # Add calculated fields using breakeven analyzer
    from .breakeven_analysis import BreakevenAnalyzer
    
    analyzer = BreakevenAnalyzer(
        fixed_costs=departure.fixed_costs,
        variable_costs_per_person=departure.variable_costs_per_person,
        marketing_costs=departure.marketing_costs,
        price_per_person=departure.current_price_per_person,
        commission_rate=departure.commission_rate,
        max_capacity=departure.available_spots
    )
    
    # Get analysis results
    analysis = analyzer.get_breakeven_analysis(departure.slots_filled)
    cost_breakdown = analyzer.get_cost_breakdown(departure.slots_filled)
    
    # Update departure object with calculated fields
    departure.variable_costs_total = cost_breakdown['variable_costs_total']
    departure.total_costs = cost_breakdown['total_costs']
    departure.commission_amount = analysis['commission_amount_per_person'] * departure.slots_filled
    departure.net_revenue = departure.current_revenue - departure.commission_amount
    departure.contribution_margin_per_person = analysis['contribution_margin_per_person']
    departure.net_revenue_per_person = analysis['net_revenue_per_person']
    
    # Update breakeven fields if they're not set
    if not departure.breakeven_passengers:
        departure.breakeven_passengers = analysis['breakeven_passengers']
    if not departure.profit_at_capacity:
        departure.profit_at_capacity = analysis['profit_at_capacity']
    if not departure.roi_percentage:
        departure.roi_percentage = analysis['roi_percentage']
    
    context = {
        'departure': departure,
        'bookings': bookings,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/departure_detail.html', context)

@login_required
@require_tour_operator
def delete_departure(request, departure_id):
    """Delete a departure"""
    tour_operator = request.tour_operator
    departure = get_object_or_404(TourDeparture, id=departure_id, tour__tour_operator=tour_operator)
    
    if request.method == 'POST':
        departure.delete()
        messages.success(request, f"Departure for '{departure.tour.title}' on {departure.departure_date} has been deleted.")
        return redirect('departures')
    
    context = {
        'departure': departure,
        'tour_operator': tour_operator,
    }
    return render(request, 'core/delete_departure_confirm.html', context)

@login_required
@require_tour_operator
def analytics(request):
    """AI-powered analytics dashboard"""
    tour_operator = request.tour_operator
    
    # Get AI analytics
    analytics_data = AIAnalytics.objects.filter(
        tour_operator=tour_operator
    ).order_by('-generated_date')
    
    # Revenue trends
    monthly_revenue = Booking.objects.filter(
        tour_operator=tour_operator,
        status='confirmed',
        booking_date__year=timezone.now().year
    ).extra(
        select={'month': "EXTRACT(month FROM booking_date)"}
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')
    
    context = {
        'analytics_data': analytics_data,
        'monthly_revenue': monthly_revenue,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/analytics.html', context)

@login_required
@require_tour_operator
def settings(request):
    """Tour operator settings"""
    tour_operator = request.tour_operator
    
    if request.method == 'POST':
        form = TourOperatorForm(request.POST, instance=tour_operator)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated successfully.")
            return redirect('settings')
    else:
        form = TourOperatorForm(instance=tour_operator)
    
    context = {
        'form': form,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/settings.html', context)

# API endpoints for AI processing
@csrf_exempt
def ai_processing_webhook(request):
    """Webhook for AI processing results"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            job_id = data.get('job_id')
            status = data.get('status')
            result_data = data.get('result_data', {})
            error_message = data.get('error_message')
            
            job = AIProcessingJob.objects.get(id=job_id)
            job.status = status
            job.result_data = result_data
            job.error_message = error_message
            
            if status in ['completed', 'failed']:
                job.completed_date = timezone.now()
            
            job.save()
            
            # Update document processing status
            if status == 'completed':
                job.document.processing_status = 'completed'
                job.document.extracted_data = result_data
                job.document.confidence_score = result_data.get('confidence_score', 0)
                job.document.processed_date = timezone.now()
                job.document.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def login(request):
    """Login with tour operator association"""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                auth_login(request, user)
                
                # Allow superusers to login without tour operator requirement
                if user.is_superuser:
                    return redirect('dashboard')
                
                # Check if regular user has tour operator access
                tour_operator = get_user_tour_operator(user)
                if tour_operator:
                    return redirect('dashboard')
                else:
                    messages.error(request, "You don't have access to any tour operator account.")
                    auth_logout(request)
                    return redirect('login')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})

def logout(request):
    """Logout user"""
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')
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
    
    # Basic metrics
    total_customers = Customer.objects.filter(tour_operator=tour_operator).count()
    total_tours = Tour.objects.filter(tour_operator=tour_operator).count()
    total_bookings = Booking.objects.filter(tour_operator=tour_operator).count()
    
    # Revenue calculations
    total_revenue = Booking.objects.filter(
        tour_operator=tour_operator, 
        status='confirmed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Recent activity
    recent_bookings = Booking.objects.filter(
        tour_operator=tour_operator
    ).order_by('-booking_date')[:5]
    
    upcoming_departures = TourDeparture.objects.filter(
        tour__tour_operator=tour_operator,
        departure_date__gte=timezone.now().date(),
        status='scheduled'
    ).order_by('departure_date')[:5]
    
    # AI analytics
    recent_analytics = AIAnalytics.objects.filter(
        tour_operator=tour_operator
    ).order_by('-generated_date')[:3]
    
    # Document processing status
    pending_documents = DocumentUpload.objects.filter(
        tour_operator=tour_operator,
        processing_status='pending'
    ).count()
    
    processing_documents = DocumentUpload.objects.filter(
        tour_operator=tour_operator,
        processing_status='processing'
    ).count()
    
    context = {
        'tour_operator': tour_operator,
        'total_customers': total_customers,
        'total_tours': total_tours,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'recent_bookings': recent_bookings,
        'upcoming_departures': upcoming_departures,
        'recent_analytics': recent_analytics,
        'pending_documents': pending_documents,
        'processing_documents': processing_documents,
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
    
    context = {
        'customers': customers,
        'tour_operator': tour_operator,
        'segment_filter': segment_filter,
        'search_query': search_query,
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
    
    # Add calculated fields to each departure for template use
    for departure in departures:
        departure.commission_amount = (departure.current_price_per_person * departure.commission_rate / 100) * departure.slots_filled
        departure.net_revenue = departure.current_revenue - departure.commission_amount
        departure.remaining_spots = departure.available_spots - departure.slots_filled
        departure.total_costs = departure.fixed_costs + departure.marketing_costs + (departure.variable_costs_per_person * departure.slots_filled)
    
    context = {
        'departures': departures,
        'tour_operator': tour_operator,
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
        'profitable_count': profitable_count,
        'total_departures': total_departures,
    }
    
    return render(request, 'core/departures.html', context)

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
    
    context = {
        'departure': departure,
        'bookings': bookings,
        'tour_operator': tour_operator,
    }
    
    return render(request, 'core/departure_detail.html', context)

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
                
                # Check if user has tour operator access
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
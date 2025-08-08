from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from core.models import AIProcessingJob, DocumentUpload, Tour, TourOperator
from core.gemini_ai_processing import GeminiAIProcessor, process_document_with_gemini
import json
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process pending AI jobs using Gemini AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--use-mock',
            action='store_true',
            help='Use mock data instead of real Gemini AI (for testing)',
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='Gemini API key (overrides settings)',
        )

    def handle(self, *args, **options):
        # Get all pending jobs
        pending_jobs = AIProcessingJob.objects.filter(status='queued')
        
        if not pending_jobs.exists():
            self.stdout.write(self.style.WARNING('No pending AI jobs found.'))
            return
        
        self.stdout.write(f'Processing {pending_jobs.count()} AI jobs...')
        
        # Initialize AI processor
        use_mock = options['use_mock']
        api_key = options['api_key'] or getattr(settings, 'GEMINI_API_KEY', None)
        
        if not use_mock:
            if not api_key:
                self.stdout.write(
                    self.style.ERROR('Gemini API key not found. Set GEMINI_API_KEY in settings or use --api-key parameter.')
                )
                return
            
            try:
                ai_processor = GeminiAIProcessor(api_key)
                self.stdout.write(self.style.SUCCESS('✅ Gemini AI processor initialized'))
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to initialize Gemini AI: {e}')
                )
                return
        
        for job in pending_jobs:
            self.process_single_job(job, use_mock, ai_processor)
        
        self.stdout.write(self.style.SUCCESS('Successfully processed all AI jobs!'))

    def process_single_job(self, job, use_mock=False, ai_processor=None):
        """Process a single AI job"""
        self.stdout.write(f'Processing job {job.id} for document: {job.document.file_name}')
        
        # Update job status to processing
        job.status = 'processing'
        job.save()
        
        try:
            if job.job_type == 'document_extraction':
                if use_mock:
                    # Use mock data for testing
                    extracted_data = self.generate_mock_tour_data(job.document.file_name)
                else:
                    # Use real Gemini AI
                    extracted_data = self.process_with_gemini(job.document, ai_processor)
                
                # Update job with results
                job.result_data = extracted_data
                job.status = 'completed'
                job.completed_date = timezone.now()
                job.save()
                
                # Update document
                job.document.processing_status = 'completed'
                job.document.extracted_data = extracted_data
                job.document.confidence_score = extracted_data.get('extraction_confidence', 0) * 100
                job.document.processed_date = timezone.now()
                job.document.save()
                
                # Create tours from the extracted data
                self.create_tours_from_extraction(job.document, extracted_data)
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Job {job.id} completed successfully!')
                )
            else:
                # For other job types, just mark as completed
                job.status = 'completed'
                job.completed_date = timezone.now()
                job.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Job {job.id} completed!')
                )
                
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
            
            # Update document status
            job.document.processing_status = 'failed'
            job.document.processing_errors = str(e)
            job.document.save()
            
            self.stdout.write(
                self.style.ERROR(f'❌ Error processing job {job.id}: {str(e)}')
            )

    def process_with_gemini(self, document: DocumentUpload, ai_processor: GeminiAIProcessor):
        """Process document with real Gemini AI"""
        try:
            # Debug: Show file path and existence
            print(f"🔍 Processing file: {document.file_path}")
            print(f"🔍 File exists: {os.path.exists(document.file_path)}")
            
            # Read the actual uploaded file
            if os.path.exists(document.file_path):
                document_content = ai_processor.analyze_document_content(document.file_path)
                print(f"📄 Read document content: {len(document_content)} characters")
                
                # Debug: Show first 200 characters to verify content
                print(f"📄 Content preview: {document_content[:200]}...")
                
                if len(document_content) < 100:
                    print(f"⚠️ Document content seems too short: {len(document_content)} characters")
                    return {
                        "extraction_confidence": 0.0,
                        "extracted_tours": [],
                        "processing_notes": [f"Document content too short: {len(document_content)} characters"]
                    }
            else:
                print(f"⚠️ File not found: {document.file_path}")
                return {
                    "extraction_confidence": 0.0,
                    "extracted_tours": [],
                    "processing_notes": [f"File not found: {document.file_path}"] #adding a comment for commit
                }
            
            # Process with Gemini AI
            print("🤖 Processing with Gemini AI...")
            extracted_data = ai_processor.extract_tour_information(document_content, document.file_type)
            
            # Debug: Show extraction results
            print(f"🤖 AI Confidence: {extracted_data.get('extraction_confidence', 0)}")
            print(f"🤖 Tours found: {len(extracted_data.get('extracted_tours', []))}")
            
            # Add processing metadata
            extracted_data['processing_metadata'] = {
                'processed_by': 'Gemini AI',
                'processing_time': timezone.now().isoformat(),
                'document_id': str(document.id),
                'file_type': document.file_type
            }
            
            return extracted_data
            
        except Exception as e:
            import traceback
            print(f"❌ Error processing document: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return {
                "extraction_confidence": 0.0,
                "extracted_tours": [],
                "processing_notes": [f"Processing failed: {str(e)}"]
            }

    def generate_mock_tour_data(self, filename):
        """Generate realistic mock tour data based on filename"""
        import random
        
        # Extract some info from filename for realism
        filename_lower = filename.lower()
        
        # Determine destination based on filename
        destinations = ['Paris', 'London', 'Rome', 'Barcelona', 'Amsterdam', 'Prague', 'Vienna', 'Budapest']
        destination = random.choice(destinations)
        
        # Determine tour type based on filename
        if 'city' in filename_lower or 'urban' in filename_lower:
            tour_type = 'City Tour'
            duration = random.randint(1, 3)
        elif 'adventure' in filename_lower or 'hiking' in filename_lower:
            tour_type = 'Adventure Tour'
            duration = random.randint(3, 7)
        elif 'cultural' in filename_lower or 'heritage' in filename_lower:
            tour_type = 'Cultural Tour'
            duration = random.randint(2, 5)
        else:
            tour_type = 'Discovery Tour'
            duration = random.randint(2, 4)
        
        # Generate pricing
        base_price = random.randint(50, 200)
        price_per_person = base_price * duration
        
        # Generate mock extraction data
        mock_data = {
            'extraction_confidence': random.uniform(85, 98),
            'extracted_tours': [
                {
                    'title': f'{tour_type} - {destination}',
                    'destination': destination,
                    'duration_days': duration,
                    'pricing_type': 'per_person',
                    'price_per_person': price_per_person,
                    'max_group_size': random.randint(8, 20),
                    'description': f'Experience the best of {destination} with our comprehensive {tour_type.lower()}. Discover hidden gems and iconic landmarks.',
                    'highlights': f'• Guided tour of {destination}\n• Local expert guide\n• Small group experience\n• Hotel pickup and drop-off',
                    'included_services': f'• Professional guide\n• Transportation\n• Entrance fees\n• Lunch (for {duration}+ day tours)',
                    'excluded_services': '• Personal expenses\n• Tips for guide\n• Optional activities',
                    'difficulty_level': random.choice(['easy', 'moderate']),
                    'seasonal_demand': random.choice(['high', 'medium', 'year_round']),
                    'cost_per_person': price_per_person * 0.6,  # 60% of price as cost
                    'operational_costs': random.randint(200, 500),
                }
            ],
            'processing_notes': [
                'Successfully extracted tour information from document',
                'Pricing information detected and validated',
                'Tour highlights and services identified',
                'Ready for review and publication'
            ],
            'processing_metadata': {
                'processed_by': 'Mock AI (Testing)',
                'processing_time': timezone.now().isoformat(),
                'note': 'This is mock data for testing purposes'
            }
        }
        
        return mock_data

    def create_tours_from_extraction(self, document: DocumentUpload, extracted_data: dict):
        """Create a single tour from extracted data (main tour only)"""
        try:
            tours_data = extracted_data.get('extracted_tours', [])
            
            if not tours_data:
                self.stdout.write(self.style.WARNING("⚠️ No tours found in extracted data"))
                return
            
            # Only create the main tour (first one)
            tour_data = tours_data[0]
            
            # Get the tour operator from the document
            tour_operator = document.tour_operator
            
            # Create the tour
            tour = Tour.objects.create(
                tour_operator=tour_operator,
                source_document=document,
                title=tour_data['title'],
                destination=tour_data['destination'],
                duration_days=tour_data['duration_days'],
                pricing_type=tour_data['pricing_type'],
                price_per_person=tour_data.get('price_per_person') or 0,
                price_per_group=tour_data.get('price_per_group') or 0,
                max_group_size=tour_data.get('max_group_size') or 15,  # Default to 15 if None or not provided
                description=tour_data.get('description') or '',
                highlights=tour_data.get('highlights') or '',
                included_services=tour_data.get('included_services') or '',
                excluded_services=tour_data.get('excluded_services') or '',
                difficulty_level=tour_data.get('difficulty_level') or 'moderate',
                seasonal_demand=tour_data.get('seasonal_demand') or 'medium',
                cost_per_person=tour_data.get('cost_per_person') or 0,
                operational_costs=tour_data.get('operational_costs') or 0,
                status='draft',  # Start as draft for review
                ai_extraction_confidence=extracted_data.get('extraction_confidence', 0) * 100,
                ai_processed_date=timezone.now()
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Created main tour: {tour.title}')
            )
            
            # Store additional tours info in document for reference
            if len(tours_data) > 1:
                additional_tours = tours_data[1:]
                document.processing_notes = f"Additional tours found: {len(additional_tours)}. Only main tour created. Upload separate documents for extensions."
                document.save()
                self.stdout.write(f"ℹ️ Found {len(additional_tours)} additional tours - upload as separate documents")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating tour: {str(e)}')
            )

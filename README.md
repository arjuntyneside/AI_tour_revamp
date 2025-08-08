# AI-Powered Tour Operator B2B SaaS Platform

A comprehensive B2B SaaS platform for tour operators with AI-powered document processing, tour management, and business intelligence.

## Features

- **AI Document Processing**: Upload tour brochures and automatically extract tour information
- **Multi-Tenant Architecture**: Each tour operator gets their own isolated workspace
- **Tour Management**: Complete tour lifecycle management with AI insights
- **Customer Segmentation**: AI-powered customer analysis and segmentation
- **Business Intelligence**: Revenue analytics, demand forecasting, and operational insights
- **Booking Management**: Comprehensive booking system with AI risk assessment

## Setup Instructions

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd u_d_internal_tool

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the template file
cp env_template.txt .env
```

Edit the `.env` file with your configuration:

```env
# Django Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# Gemini AI Settings
GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

### 4. Database Setup

```bash
# Create database migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Setup demo tour operator (optional)
python manage.py setup_demo
```

### 5. Run the Application

```bash
# Start development server
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the application.

## Usage

### AI Document Processing

1. **Upload Documents**: Go to `/documents/upload/` and upload tour brochures
2. **Process with AI**: Run `python manage.py process_ai_jobs` to process documents
3. **Review Results**: Check `/documents/processing/` for processing status
4. **Create Tours**: Tours are automatically created from extracted data

### Processing Commands

**With Real Gemini AI:**
```bash
python manage.py process_ai_jobs
```

**With Mock Data (for testing):**
```bash
python manage.py process_ai_jobs --use-mock
```

**With Custom API Key:**
```bash
python manage.py process_ai_jobs --api-key YOUR_API_KEY
```

## Project Structure

```
u_d_internal_tool/
├── core/
│   ├── models.py              # Database models
│   ├── views.py               # View logic
│   ├── forms.py               # Form definitions
│   ├── admin.py               # Admin interface
│   ├── gemini_ai_processing.py # Gemini AI integration
│   ├── management/commands/   # Custom management commands
│   └── templates/core/        # HTML templates
├── undiscovered_destinations/
│   ├── settings.py            # Django settings
│   ├── urls.py                # URL configuration
│   └── wsgi.py                # WSGI configuration
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create this)
├── env_template.txt          # Environment variables template
└── README.md                 # This file
```

## Key Models

- **TourOperator**: Multi-tenant tour operator accounts
- **DocumentUpload**: Uploaded documents for AI processing
- **AIProcessingJob**: AI processing job tracking
- **Tour**: Tour information with AI insights
- **Customer**: Customer data with AI segmentation
- **Booking**: Booking management with AI risk assessment
- **AIAnalytics**: AI-generated business insights

## AI Integration

The platform uses Google's Gemini AI for:

- **Document Extraction**: Extract tour information from brochures
- **Data Structuring**: Convert unstructured data to structured tour records
- **Confidence Scoring**: Assess extraction quality
- **Error Handling**: Graceful fallback when AI processing fails

## Security

- **Environment Variables**: All sensitive data stored in `.env` file
- **Multi-Tenant Isolation**: Data isolation between tour operators
- **API Key Protection**: Secure API key management
- **Input Validation**: Comprehensive file and data validation

## Development

### Adding New AI Features

1. Extend `GeminiAIProcessor` in `gemini_ai_processing.py`
2. Add new job types in `AIProcessingJob` model
3. Update processing logic in management commands
4. Add UI components in templates

### Customizing AI Prompts

Edit the `extraction_prompt` in `GeminiAIProcessor` to customize AI behavior for different document types.

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Use a production database (PostgreSQL recommended)
3. Configure static file serving
4. Set up proper logging
5. Use environment-specific settings

## Support

For issues and questions:
- Check the Django logs for error details
- Verify API keys are correctly configured
- Ensure all dependencies are installed
- Check file permissions for document uploads

## License

[Add your license information here]

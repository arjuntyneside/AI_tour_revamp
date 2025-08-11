from django.core.management.base import BaseCommand
from core.models import TourOperator
from core.ai_financial_insights import get_ai_financial_insights

class Command(BaseCommand):
    help = 'Test the AI financial insights module'

    def handle(self, *args, **options):
        self.stdout.write("Testing AI Financial Insights Module...")
        
        # Get the first tour operator
        tour_operator = TourOperator.objects.first()
        
        if not tour_operator:
            self.stdout.write(
                self.style.ERROR("No tour operator found. Please run setup_demo first.")
            )
            return
        
        self.stdout.write(f"Analyzing insights for: {tour_operator.name}")
        
        # Get AI insights
        insights = get_ai_financial_insights(tour_operator)
        
        # Display summary
        self.stdout.write(f"\n=== AI Insights Summary ===")
        self.stdout.write(f"Total Insights: {insights['total_insights']}")
        self.stdout.write(f"Total Recommendations: {insights['total_recommendations']}")
        self.stdout.write(f"High Priority Items: {insights['high_priority_count']}")
        
        # Display each insight
        for insight in insights['insights']:
            self.stdout.write(f"\n=== {insight['title']} ===")
            self.stdout.write(f"Priority: {insight['priority'].upper()}")
            self.stdout.write(f"Risk Level: {insight['risk_level']}")
            
            # Display metrics
            if insight['metrics']:
                self.stdout.write("Key Metrics:")
                for key, value in insight['metrics'].items():
                    if isinstance(value, float):
                        self.stdout.write(f"  {key.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        self.stdout.write(f"  {key.replace('_', ' ').title()}: {value}")
            
            # Display recommendations
            if insight['recommendations']:
                self.stdout.write("Recommendations:")
                for i, rec in enumerate(insight['recommendations'], 1):
                    self.stdout.write(f"  {i}. {rec['title']}")
                    self.stdout.write(f"     Description: {rec['description']}")
                    self.stdout.write(f"     Action: {rec['action']}")
                    self.stdout.write(f"     Impact: {rec['impact']}")
                    
                    if 'departures' in rec and rec['departures']:
                        self.stdout.write(f"     Affected Departures: {len(rec['departures'])}")
            else:
                self.stdout.write("  No specific recommendations at this time.")
        
        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ AI financial insights module tested successfully!"
            )
        )

from django.core.management.base import BaseCommand
from core.models import TourOperator
from core.gemini_ai_insights import get_gemini_ai_insights
import json

class Command(BaseCommand):
    help = 'Test the Gemini AI-powered financial insights'

    def handle(self, *args, **options):
        self.stdout.write("Testing Gemini AI Financial Insights...")
        
        # Get the first tour operator
        tour_operator = TourOperator.objects.first()
        
        if not tour_operator:
            self.stdout.write(
                self.style.ERROR("No tour operator found. Please run setup_demo first.")
            )
            return
        
        self.stdout.write(f"Analyzing insights for: {tour_operator.name}")
        
        # Get Gemini AI insights
        insights = get_gemini_ai_insights(tour_operator)
        
        # Display summary
        self.stdout.write(f"\n=== Gemini AI Insights Summary ===")
        self.stdout.write(f"AI Generated: {insights.get('ai_generated', False)}")
        self.stdout.write(f"Total Insights: {insights['total_insights']}")
        self.stdout.write(f"Total Recommendations: {insights['total_recommendations']}")
        self.stdout.write(f"High Priority Items: {insights['high_priority_count']}")
        
        # Display overall assessment if available
        if 'overall_assessment' in insights:
            assessment = insights['overall_assessment']
            self.stdout.write(f"\n=== Overall Business Assessment ===")
            self.stdout.write(f"Business Health: {assessment.get('business_health', 'Unknown')}")
            
            if 'key_strengths' in assessment:
                self.stdout.write("Key Strengths:")
                for strength in assessment['key_strengths']:
                    self.stdout.write(f"  ✅ {strength}")
            
            if 'key_concerns' in assessment:
                self.stdout.write("Key Concerns:")
                for concern in assessment['key_concerns']:
                    self.stdout.write(f"  ⚠️ {concern}")
            
            if 'immediate_priorities' in assessment:
                self.stdout.write("Immediate Priorities:")
                for priority in assessment['immediate_priorities']:
                    self.stdout.write(f"  🎯 {priority}")
        
        # Display each insight
        for i, insight in enumerate(insights['insights'], 1):
            self.stdout.write(f"\n=== Insight {i}: {insight['title']} ===")
            self.stdout.write(f"Type: {insight.get('type', 'Unknown')}")
            self.stdout.write(f"Priority: {insight['priority'].upper()}")
            self.stdout.write(f"Risk Level: {insight['risk_level']}")
            self.stdout.write(f"Summary: {insight.get('summary', 'No summary')}")
            
            # Display detailed analysis
            if 'detailed_analysis' in insight:
                analysis = insight['detailed_analysis']
                if len(analysis) > 200:
                    analysis = analysis[:200] + "..."
                self.stdout.write(f"Analysis: {analysis}")
            
            # Display recommendations
            if insight['recommendations']:
                self.stdout.write("Recommendations:")
                for j, rec in enumerate(insight['recommendations'], 1):
                    self.stdout.write(f"  {j}. {rec['title']}")
                    self.stdout.write(f"     Description: {rec['description']}")
                    self.stdout.write(f"     Action: {rec['action']}")
                    self.stdout.write(f"     Impact: {rec['impact']}")
                    self.stdout.write(f"     Timeline: {rec.get('timeline', 'Not specified')}")
                    
                    if 'implementation_steps' in rec:
                        self.stdout.write("     Implementation Steps:")
                        for step in rec['implementation_steps']:
                            self.stdout.write(f"       - {step}")
                    
                    if 'expected_outcome' in rec:
                        self.stdout.write(f"     Expected Outcome: {rec['expected_outcome']}")
                    
                    if 'affected_departures' in rec and rec['affected_departures']:
                        self.stdout.write(f"     Affected Departures: {len(rec['affected_departures'])}")
            else:
                self.stdout.write("  No specific recommendations at this time.")
            
            # Display metrics
            if 'metrics' in insight and insight['metrics']:
                self.stdout.write("Key Metrics:")
                for key, value in insight['metrics'].items():
                    if isinstance(value, float):
                        self.stdout.write(f"  {key.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        self.stdout.write(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Display data summary
        if 'data_summary' in insights:
            summary = insights['data_summary']
            self.stdout.write(f"\n=== Data Summary ===")
            for key, value in summary.items():
                if isinstance(value, float):
                    self.stdout.write(f"{key.replace('_', ' ').title()}: {value:.2f}")
                else:
                    self.stdout.write(f"{key.replace('_', ' ').title()}: {value}")
        
        if insights.get('ai_generated', False):
            self.stdout.write(
                self.style.SUCCESS(
                    "\n✅ Real Gemini AI-powered insights generated successfully!"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️ Using fallback insights. Please configure GEMINI_API_KEY for real AI analysis."
                )
            )

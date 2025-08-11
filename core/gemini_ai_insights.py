"""
Gemini AI Financial Insights Module

This module provides real AI-powered financial analysis and recommendations
for tour operators using Google Gemini AI.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from core.models import TourDeparture, Tour
from core.breakeven_analysis import BreakevenAnalyzer
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
import google.generativeai as genai
import json
import os
from decouple import config


class GeminiAIFinancialInsights:
    """Real AI-powered financial insights using Google Gemini"""
    
    def __init__(self, tour_operator):
        self.tour_operator = tour_operator
        self.departures = TourDeparture.objects.filter(tour__tour_operator=tour_operator)
        self.tours = Tour.objects.filter(tour_operator=tour_operator)
        
        # Initialize Gemini AI
        api_key = config('GEMINI_API_KEY', default='')
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
    
    def _prepare_data_for_ai(self) -> Dict:
        """Prepare comprehensive data for AI analysis"""
        data = {
            'tour_operator': {
                'name': self.tour_operator.name,
                'total_departures': self.departures.count(),
                'total_tours': self.tours.count(),
            },
            'departures': [],
            'summary_metrics': {},
            'breakeven_analysis': {}
        }
        
        # Collect detailed departure data
        for departure in self.departures:
            # Calculate breakeven metrics
            analyzer = BreakevenAnalyzer(
                fixed_costs=departure.fixed_costs,
                variable_costs_per_person=departure.variable_costs_per_person,
                marketing_costs=departure.marketing_costs,
                price_per_person=departure.current_price_per_person,
                commission_rate=departure.commission_rate,
                max_capacity=departure.available_spots
            )
            
            analysis = analyzer.get_breakeven_analysis(departure.slots_filled)
            cost_breakdown = analyzer.get_cost_breakdown(departure.slots_filled)
            
            departure_data = {
                'id': str(departure.id),
                'tour_title': departure.tour.title,
                'departure_date': departure.departure_date.isoformat(),
                'days_until_departure': (departure.departure_date - timezone.now().date()).days,
                'pricing': {
                    'current_price_per_person': float(departure.current_price_per_person),
                    'discounted_price_per_person': float(departure.discounted_price_per_person) if departure.discounted_price_per_person else None,
                    'commission_rate': float(departure.commission_rate),
                },
                'capacity': {
                    'total_capacity': departure.available_spots,
                    'slots_filled': departure.slots_filled,
                    'occupancy_rate': (departure.slots_filled / departure.available_spots * 100) if departure.available_spots else 0,
                    'remaining_spots': departure.available_spots - departure.slots_filled,
                },
                'costs': {
                    'fixed_costs': float(departure.fixed_costs),
                    'variable_costs_per_person': float(departure.variable_costs_per_person),
                    'marketing_costs': float(departure.marketing_costs),
                    'total_costs': float(cost_breakdown['total_costs']),
                },
                'financial_metrics': {
                    'current_revenue': float(departure.current_revenue),
                    'current_profit': float(departure.current_profit),
                    'breakeven_passengers': analysis['breakeven_passengers'],
                    'roi_percentage': float(analysis['roi_percentage']),
                    'is_profitable': analysis['is_profitable'],
                    'contribution_margin_per_person': float(analysis['contribution_margin_per_person']),
                    'net_revenue_per_person': float(analysis['net_revenue_per_person']),
                },
                'status': {
                    'is_profitable': analysis['is_profitable'],
                    'breakeven_achieved': analysis['breakeven_passengers'] and departure.slots_filled >= analysis['breakeven_passengers'],
                    'high_demand': departure.slots_filled / departure.available_spots > 0.8 if departure.available_spots else False,
                    'low_demand': departure.slots_filled / departure.available_spots < 0.3 if departure.available_spots else False,
                }
            }
            data['departures'].append(departure_data)
        
        # Calculate summary metrics
        if data['departures']:
            total_revenue = sum(d['financial_metrics']['current_revenue'] for d in data['departures'])
            total_profit = sum(d['financial_metrics']['current_profit'] for d in data['departures'])
            total_costs = sum(d['costs']['total_costs'] for d in data['departures'])
            total_capacity = sum(d['capacity']['total_capacity'] for d in data['departures'])
            total_bookings = sum(d['capacity']['slots_filled'] for d in data['departures'])
            
            data['summary_metrics'] = {
                'total_revenue': total_revenue,
                'total_profit': total_profit,
                'total_costs': total_costs,
                'overall_profit_margin': (total_profit / total_revenue * 100) if total_revenue else 0,
                'overall_occupancy_rate': (total_bookings / total_capacity * 100) if total_capacity else 0,
                'profitable_departures': len([d for d in data['departures'] if d['financial_metrics']['is_profitable']]),
                'unprofitable_departures': len([d for d in data['departures'] if not d['financial_metrics']['is_profitable']]),
                'high_demand_departures': len([d for d in data['departures'] if d['status']['high_demand']]),
                'low_demand_departures': len([d for d in data['departures'] if d['status']['low_demand']]),
                'breakeven_achieved_departures': len([d for d in data['departures'] if d['status']['breakeven_achieved']]),
            }
        
        return data
    
    def _generate_ai_prompt(self, data: Dict) -> str:
        """Generate comprehensive prompt for Gemini AI"""
        prompt = f"""
You are an expert financial analyst specializing in tour operator businesses. Analyze the following tour operator data and provide actionable insights and recommendations.

TOUR OPERATOR DATA:
{json.dumps(data, indent=2)}

ANALYSIS REQUIREMENTS:
1. **Pricing Strategy Analysis**: Identify pricing opportunities, margin issues, and optimization strategies
2. **Demand & Capacity Analysis**: Analyze booking patterns, occupancy rates, and capacity optimization
3. **Cost Structure Analysis**: Identify cost inefficiencies and optimization opportunities
4. **Profitability Analysis**: Assess overall profitability and identify improvement areas
5. **Risk Assessment**: Identify potential risks and mitigation strategies
6. **Strategic Recommendations**: Provide specific, actionable recommendations

OUTPUT FORMAT:
Provide your analysis in the following JSON format:

{{
    "insights": [
        {{
            "type": "pricing_optimization|demand_forecasting|cost_optimization|profitability_trends|risk_assessment|strategic_recommendations",
            "title": "Clear, descriptive title",
            "priority": "high|medium|low",
            "risk_level": "high|medium|low",
            "summary": "Brief summary of the insight",
            "detailed_analysis": "Comprehensive analysis with specific data points",
            "recommendations": [
                {{
                    "title": "Specific recommendation title",
                    "description": "Detailed description of the recommendation",
                    "action": "Specific action to take",
                    "impact": "high|medium|low",
                    "implementation_steps": ["Step 1", "Step 2", "Step 3"],
                    "expected_outcome": "What to expect after implementation",
                    "affected_departures": ["departure_id_1", "departure_id_2"],
                    "timeline": "immediate|short_term|long_term"
                }}
            ],
            "metrics": {{
                "key_metric_1": "value",
                "key_metric_2": "value"
            }}
        }}
    ],
    "overall_assessment": {{
        "business_health": "excellent|good|fair|poor",
        "key_strengths": ["strength1", "strength2"],
        "key_concerns": ["concern1", "concern2"],
        "immediate_priorities": ["priority1", "priority2"],
        "long_term_strategy": "Strategic direction for the business"
    }}
}}

Focus on providing specific, actionable insights that can directly improve the tour operator's financial performance. Use the actual data provided and give concrete recommendations with implementation steps.
"""
        return prompt
    
    def get_ai_insights(self) -> Dict:
        """Get AI-powered insights using Gemini"""
        if not self.model:
            return self._get_fallback_insights()
        
        try:
            # Prepare data for AI analysis
            data = self._prepare_data_for_ai()
            
            # Generate AI prompt
            prompt = self._generate_ai_prompt(data)
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            try:
                ai_analysis = json.loads(response.text)
                return self._process_ai_response(ai_analysis, data)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract insights from text
                return self._extract_insights_from_text(response.text, data)
                
        except Exception as e:
            print(f"AI analysis failed: {e}")
            return self._get_fallback_insights()
    
    def _process_ai_response(self, ai_analysis: Dict, original_data: Dict) -> Dict:
        """Process and validate AI response"""
        processed_insights = {
            'total_insights': len(ai_analysis.get('insights', [])),
            'total_recommendations': sum(len(insight.get('recommendations', [])) for insight in ai_analysis.get('insights', [])),
            'high_priority_count': len([i for i in ai_analysis.get('insights', []) if i.get('priority') == 'high']),
            'insights': ai_analysis.get('insights', []),
            'overall_assessment': ai_analysis.get('overall_assessment', {}),
            'ai_generated': True,
            'data_summary': {
                'total_departures': original_data['summary_metrics'].get('total_revenue', 0),
                'total_revenue': original_data['summary_metrics'].get('total_revenue', 0),
                'total_profit': original_data['summary_metrics'].get('total_profit', 0),
                'overall_occupancy': original_data['summary_metrics'].get('overall_occupancy_rate', 0),
            }
        }
        
        return processed_insights
    
    def _extract_insights_from_text(self, text: str, data: Dict) -> Dict:
        """Extract insights from AI text response when JSON parsing fails"""
        # This is a fallback method to extract insights from text
        insights = {
            'total_insights': 1,
            'total_recommendations': 1,
            'high_priority_count': 1,
            'insights': [{
                'type': 'ai_analysis',
                'title': '🤖 AI Analysis',
                'priority': 'high',
                'risk_level': 'medium',
                'summary': 'AI analysis completed',
                'detailed_analysis': text[:500] + "..." if len(text) > 500 else text,
                'recommendations': [{
                    'title': 'Review AI Analysis',
                    'description': 'The AI has provided detailed analysis of your tour operations.',
                    'action': 'Review Analysis',
                    'impact': 'high',
                    'implementation_steps': ['Review the detailed analysis above', 'Implement recommended changes', 'Monitor results'],
                    'expected_outcome': 'Improved financial performance based on AI recommendations',
                    'affected_departures': [],
                    'timeline': 'immediate'
                }],
                'metrics': data['summary_metrics']
            }],
            'overall_assessment': {
                'business_health': 'good',
                'key_strengths': ['AI analysis available'],
                'key_concerns': ['Review AI recommendations'],
                'immediate_priorities': ['Implement AI recommendations'],
                'long_term_strategy': 'Continue using AI for business optimization'
            },
            'ai_generated': True,
            'data_summary': data['summary_metrics']
        }
        
        return insights
    
    def _get_fallback_insights(self) -> Dict:
        """Fallback insights when AI is not available"""
        return {
            'total_insights': 1,
            'total_recommendations': 1,
            'high_priority_count': 1,
            'insights': [{
                'type': 'system_notice',
                'title': '⚠️ AI Analysis Unavailable',
                'priority': 'medium',
                'risk_level': 'low',
                'summary': 'Gemini AI is not configured',
                'detailed_analysis': 'Please configure GEMINI_API_KEY in your .env file to enable AI-powered insights.',
                'recommendations': [{
                    'title': 'Configure AI',
                    'description': 'Set up Gemini AI for intelligent insights',
                    'action': 'Add API Key',
                    'impact': 'medium',
                    'implementation_steps': ['Add GEMINI_API_KEY to .env file', 'Restart the application'],
                    'expected_outcome': 'AI-powered financial insights',
                    'affected_departures': [],
                    'timeline': 'immediate'
                }],
                'metrics': {}
            }],
            'overall_assessment': {
                'business_health': 'unknown',
                'key_strengths': ['Basic analytics available'],
                'key_concerns': ['AI analysis not available'],
                'immediate_priorities': ['Configure AI'],
                'long_term_strategy': 'Enable AI for business optimization'
            },
            'ai_generated': False,
            'data_summary': {}
        }
    
    def get_insight_summary(self) -> Dict:
        """Get AI-powered insight summary"""
        return self.get_ai_insights()


# Convenience function
def get_gemini_ai_insights(tour_operator):
    """Get real AI-powered financial insights for a tour operator using Gemini"""
    analyzer = GeminiAIFinancialInsights(tour_operator)
    return analyzer.get_insight_summary()

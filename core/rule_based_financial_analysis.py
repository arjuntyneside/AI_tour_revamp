"""
AI Financial Insights Module

This module provides AI-powered financial analysis and recommendations
for tour operators based on departure data and market trends.
"""

from decimal import Decimal
from typing import Dict, List, Optional
from core.models import TourDeparture, Tour
from core.breakeven_analysis import BreakevenAnalyzer
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta


class AIFinancialInsights:
    """AI-powered financial insights and recommendations"""
    
    def __init__(self, tour_operator):
        self.tour_operator = tour_operator
        self.departures = TourDeparture.objects.filter(tour__tour_operator=tour_operator)
        self.tours = Tour.objects.filter(tour_operator=tour_operator)
    
    def analyze_pricing_optimization(self) -> Dict:
        """Analyze pricing strategies and provide optimization recommendations"""
        insights = {
            'type': 'pricing_optimization',
            'title': '💰 Pricing Optimization',
            'priority': 'high',
            'recommendations': [],
            'metrics': {},
            'risk_level': 'low'
        }
        
        # Calculate average pricing metrics
        avg_price = self.departures.aggregate(avg_price=Avg('current_price_per_person'))['avg_price'] or 0
        avg_cost = self.departures.aggregate(avg_cost=Avg('variable_costs_per_person'))['avg_cost'] or 0
        avg_margin = avg_price - avg_cost if avg_price and avg_cost else 0
        
        # Find underperforming departures
        low_margin_departures = []
        high_margin_departures = []
        
        for departure in self.departures:
            margin = departure.current_price_per_person - departure.variable_costs_per_person
            margin_percentage = (margin / departure.current_price_per_person * 100) if departure.current_price_per_person else 0
            
            if margin_percentage < 20:  # Less than 20% margin
                low_margin_departures.append({
                    'departure': departure,
                    'margin_percentage': margin_percentage,
                    'current_price': departure.current_price_per_person,
                    'suggested_price': departure.variable_costs_per_person * Decimal('1.3')  # 30% margin
                })
            elif margin_percentage > 50:  # High margin
                high_margin_departures.append(departure)
        
        # Generate recommendations
        if low_margin_departures:
            insights['recommendations'].append({
                'type': 'price_increase',
                'title': 'Consider price increases for low-margin departures',
                'description': f'{len(low_margin_departures)} departures have margins below 20%',
                'action': 'Review pricing strategy',
                'impact': 'high',
                'departures': low_margin_departures[:3]  # Top 3
            })
        
        if high_margin_departures:
            insights['recommendations'].append({
                'type': 'competitive_advantage',
                'title': 'High-margin departures identified',
                'description': f'{len(high_margin_departures)} departures have excellent margins',
                'action': 'Consider expanding similar offerings',
                'impact': 'medium',
                'departures': high_margin_departures[:3]
            })
        
        # Add metrics
        insights['metrics'] = {
            'average_price': avg_price,
            'average_margin': avg_margin,
            'average_margin_percentage': (avg_margin / avg_price * 100) if avg_price else 0,
            'low_margin_count': len(low_margin_departures),
            'high_margin_count': len(high_margin_departures)
        }
        
        return insights
    
    def analyze_demand_forecasting(self) -> Dict:
        """Analyze booking patterns and provide demand forecasting insights"""
        insights = {
            'type': 'demand_forecasting',
            'title': '📊 Demand Forecasting',
            'priority': 'medium',
            'recommendations': [],
            'metrics': {},
            'risk_level': 'medium'
        }
        
        # Analyze booking patterns
        total_capacity = sum(dep.available_spots for dep in self.departures)
        total_bookings = sum(dep.slots_filled for dep in self.departures)
        overall_occupancy = (total_bookings / total_capacity * 100) if total_capacity else 0
        
        # Find high-demand vs low-demand departures
        high_demand = []
        low_demand = []
        
        for departure in self.departures:
            occupancy_rate = (departure.slots_filled / departure.available_spots * 100) if departure.available_spots else 0
            
            if occupancy_rate > 80:
                high_demand.append({
                    'departure': departure,
                    'occupancy_rate': occupancy_rate,
                    'days_until': (departure.departure_date - timezone.now().date()).days
                })
            elif occupancy_rate < 30:
                low_demand.append({
                    'departure': departure,
                    'occupancy_rate': occupancy_rate,
                    'days_until': (departure.departure_date - timezone.now().date()).days
                })
        
        # Generate recommendations
        if high_demand:
            insights['recommendations'].append({
                'type': 'capacity_increase',
                'title': 'High demand detected',
                'description': f'{len(high_demand)} departures are over 80% booked',
                'action': 'Consider increasing capacity',
                'impact': 'high',
                'departures': high_demand[:3]
            })
        
        if low_demand:
            insights['recommendations'].append({
                'type': 'marketing_boost',
                'title': 'Low demand departures need attention',
                'description': f'{len(low_demand)} departures are under 30% booked',
                'action': 'Increase marketing efforts',
                'impact': 'high',
                'departures': low_demand[:3]
            })
        
        # Add metrics
        insights['metrics'] = {
            'overall_occupancy': overall_occupancy,
            'high_demand_count': len(high_demand),
            'low_demand_count': len(low_demand),
            'total_capacity': total_capacity,
            'total_bookings': total_bookings
        }
        
        return insights
    
    def analyze_cost_optimization(self) -> Dict:
        """Analyze costs and provide optimization recommendations"""
        insights = {
            'type': 'cost_optimization',
            'title': '🎯 Cost Optimization',
            'priority': 'high',
            'recommendations': [],
            'metrics': {},
            'risk_level': 'low'
        }
        
        # Calculate cost metrics
        avg_fixed_costs = self.departures.aggregate(avg_fixed=Avg('fixed_costs'))['avg_fixed'] or 0
        avg_variable_costs = self.departures.aggregate(avg_variable=Avg('variable_costs_per_person'))['avg_variable'] or 0
        avg_marketing_costs = self.departures.aggregate(avg_marketing=Avg('marketing_costs'))['avg_marketing'] or 0
        
        # Find high-cost departures
        high_cost_departures = []
        cost_efficient_departures = []
        
        for departure in self.departures:
            total_cost_per_person = (
                departure.fixed_costs / departure.available_spots + 
                departure.variable_costs_per_person + 
                departure.marketing_costs / departure.available_spots
            ) if departure.available_spots else 0
            
            cost_ratio = (total_cost_per_person / departure.current_price_per_person * 100) if departure.current_price_per_person else 0
            
            if cost_ratio > 70:  # Costs are more than 70% of price
                high_cost_departures.append({
                    'departure': departure,
                    'cost_ratio': cost_ratio,
                    'total_cost_per_person': total_cost_per_person,
                    'suggested_optimizations': self._suggest_cost_optimizations(departure)
                })
            elif cost_ratio < 40:  # Very cost efficient
                cost_efficient_departures.append(departure)
        
        # Generate recommendations
        if high_cost_departures:
            insights['recommendations'].append({
                'type': 'cost_reduction',
                'title': 'High-cost departures identified',
                'description': f'{len(high_cost_departures)} departures have costs over 70% of price',
                'action': 'Review cost structure',
                'impact': 'high',
                'departures': high_cost_departures[:3]
            })
        
        if cost_efficient_departures:
            insights['recommendations'].append({
                'type': 'best_practices',
                'title': 'Cost-efficient operations found',
                'description': f'{len(cost_efficient_departures)} departures have excellent cost ratios',
                'action': 'Study and replicate best practices',
                'impact': 'medium',
                'departures': cost_efficient_departures[:3]
            })
        
        # Add metrics
        insights['metrics'] = {
            'average_fixed_costs': avg_fixed_costs,
            'average_variable_costs': avg_variable_costs,
            'average_marketing_costs': avg_marketing_costs,
            'high_cost_count': len(high_cost_departures),
            'cost_efficient_count': len(cost_efficient_departures)
        }
        
        return insights
    
    def analyze_profitability_trends(self) -> Dict:
        """Analyze profitability trends and provide strategic insights"""
        insights = {
            'type': 'profitability_trends',
            'title': '📈 Profitability Trends',
            'priority': 'high',
            'recommendations': [],
            'metrics': {},
            'risk_level': 'medium'
        }
        
        # Calculate profitability metrics
        profitable_departures = [d for d in self.departures if d.is_profitable]
        unprofitable_departures = [d for d in self.departures if not d.is_profitable]
        
        total_profit = sum(d.current_profit for d in profitable_departures)
        total_revenue = sum(d.current_revenue for d in self.departures)
        total_costs = sum(d.fixed_costs + d.marketing_costs + (d.variable_costs_per_person * d.slots_filled) for d in self.departures)
        
        overall_profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0
        
        # Find most and least profitable departures
        sorted_by_profit = sorted(self.departures, key=lambda x: x.current_profit, reverse=True)
        top_profitable = sorted_by_profit[:3] if sorted_by_profit else []
        least_profitable = sorted_by_profit[-3:] if sorted_by_profit else []
        
        # Generate recommendations
        if unprofitable_departures:
            insights['recommendations'].append({
                'type': 'profitability_improvement',
                'title': 'Unprofitable departures detected',
                'description': f'{len(unprofitable_departures)} departures are below breakeven',
                'action': 'Review pricing and costs',
                'impact': 'high',
                'departures': unprofitable_departures[:3]
            })
        
        if profitable_departures:
            insights['recommendations'].append({
                'type': 'success_replication',
                'title': 'Profitable operations identified',
                'description': f'{len(profitable_departures)} departures are profitable',
                'action': 'Replicate successful strategies',
                'impact': 'medium',
                'departures': profitable_departures[:3]
            })
        
        # Add metrics
        insights['metrics'] = {
            'profitable_count': len(profitable_departures),
            'unprofitable_count': len(unprofitable_departures),
            'overall_profit_margin': overall_profit_margin,
            'total_profit': total_profit,
            'total_revenue': total_revenue,
            'total_costs': total_costs
        }
        
        return insights
    
    def _suggest_cost_optimizations(self, departure) -> List[str]:
        """Suggest specific cost optimizations for a departure"""
        suggestions = []
        
        if departure.fixed_costs > 500:
            suggestions.append("Consider sharing fixed costs across multiple departures")
        
        if departure.variable_costs_per_person > 100:
            suggestions.append("Negotiate better rates with suppliers")
        
        if departure.marketing_costs > 50:
            suggestions.append("Optimize marketing spend with targeted campaigns")
        
        if departure.commission_rate > 15:
            suggestions.append("Review commission structure")
        
        return suggestions
    
    def get_all_insights(self) -> List[Dict]:
        """Get all AI financial insights"""
        insights = [
            self.analyze_pricing_optimization(),
            self.analyze_demand_forecasting(),
            self.analyze_cost_optimization(),
            self.analyze_profitability_trends()
        ]
        
        # Sort by priority (high first)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        insights.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return insights
    
    def get_insight_summary(self) -> Dict:
        """Get a summary of all insights"""
        all_insights = self.get_all_insights()
        
        total_recommendations = sum(len(insight['recommendations']) for insight in all_insights)
        high_priority_count = len([i for i in all_insights if i['priority'] == 'high'])
        
        return {
            'total_insights': len(all_insights),
            'total_recommendations': total_recommendations,
            'high_priority_count': high_priority_count,
            'insights': all_insights
        }


# Convenience function
def get_ai_financial_insights(tour_operator):
    """Get AI financial insights for a tour operator"""
    analyzer = AIFinancialInsights(tour_operator)
    return analyzer.get_insight_summary()

"""
Breakeven Analysis Module

This module provides functions to calculate breakeven points and financial metrics
for tour departures based on cost and pricing data.
"""

from decimal import Decimal
from typing import Dict, Optional, Tuple


class BreakevenAnalyzer:
    """Analyzes breakeven points and financial metrics for tour departures"""
    
    def __init__(self, 
                 fixed_costs: Decimal,
                 variable_costs_per_person: Decimal,
                 marketing_costs: Decimal,
                 price_per_person: Decimal,
                 commission_rate: Decimal = Decimal('0'),
                 max_capacity: int = 0):
        """
        Initialize the breakeven analyzer with cost and pricing data
        
        Args:
            fixed_costs: Fixed costs for the departure (guides, permits, equipment)
            variable_costs_per_person: Variable costs per person (accommodation, meals, transport)
            marketing_costs: Marketing and promotion costs
            price_per_person: Price charged per person
            commission_rate: Commission rate as percentage (e.g., 10.0 for 10%)
            max_capacity: Maximum number of passengers (optional, for capacity analysis)
        """
        self.fixed_costs = fixed_costs
        self.variable_costs_per_person = variable_costs_per_person
        self.marketing_costs = marketing_costs
        self.price_per_person = price_per_person
        self.commission_rate = commission_rate
        self.max_capacity = max_capacity
        
        # Calculate derived values
        self.total_fixed_costs = fixed_costs + marketing_costs
        self.commission_amount_per_person = (price_per_person * commission_rate) / Decimal('100')
        self.net_revenue_per_person = price_per_person - self.commission_amount_per_person
        self.contribution_margin_per_person = self.net_revenue_per_person - variable_costs_per_person
    
    def calculate_breakeven_passengers(self) -> Optional[int]:
        """
        Calculate the number of passengers needed to break even
        
        Returns:
            Number of passengers needed to break even, or None if not possible
        """
        if self.contribution_margin_per_person <= 0:
            return None
        
        # Breakeven = Total Fixed Costs / Contribution Margin per Person
        breakeven_decimal = self.total_fixed_costs / self.contribution_margin_per_person
        return int(breakeven_decimal) + 1  # Round up to next whole passenger
    
    def calculate_profit_at_capacity(self, current_passengers: int) -> Decimal:
        """
        Calculate profit if departure sells out to current capacity
        
        Args:
            current_passengers: Current number of passengers booked
            
        Returns:
            Profit if departure sells out
        """
        if not self.max_capacity or current_passengers >= self.max_capacity:
            return Decimal('0')
        
        breakeven_passengers = self.calculate_breakeven_passengers()
        if not breakeven_passengers or current_passengers < breakeven_passengers:
            return Decimal('0')
        
        excess_passengers = self.max_capacity - breakeven_passengers
        return excess_passengers * self.contribution_margin_per_person
    
    def calculate_current_profit(self, current_passengers: int) -> Decimal:
        """
        Calculate current profit based on actual bookings
        
        Args:
            current_passengers: Current number of passengers booked
            
        Returns:
            Current profit (0 if below breakeven)
        """
        breakeven_passengers = self.calculate_breakeven_passengers()
        if not breakeven_passengers or current_passengers < breakeven_passengers:
            return Decimal('0')
        
        excess_passengers = current_passengers - breakeven_passengers
        return excess_passengers * self.contribution_margin_per_person
    
    def calculate_roi_percentage(self, current_passengers: int) -> Decimal:
        """
        Calculate Return on Investment percentage
        
        Args:
            current_passengers: Current number of passengers booked
            
        Returns:
            ROI percentage
        """
        total_investment = self.total_fixed_costs + (current_passengers * self.variable_costs_per_person)
        if total_investment <= 0:
            return Decimal('0')
        
        profit = self.calculate_current_profit(current_passengers)
        return (profit / total_investment) * Decimal('100')
    
    def is_profitable(self, current_passengers: int) -> bool:
        """
        Check if departure is currently profitable
        
        Args:
            current_passengers: Current number of passengers booked
            
        Returns:
            True if profitable, False otherwise
        """
        breakeven_passengers = self.calculate_breakeven_passengers()
        return breakeven_passengers is not None and current_passengers >= breakeven_passengers
    
    def get_breakeven_analysis(self, current_passengers: int) -> Dict:
        """
        Get comprehensive breakeven analysis
        
        Args:
            current_passengers: Current number of passengers booked
            
        Returns:
            Dictionary with all breakeven metrics
        """
        breakeven_passengers = self.calculate_breakeven_passengers()
        current_profit = self.calculate_current_profit(current_passengers)
        profit_at_capacity = self.calculate_profit_at_capacity(current_passengers)
        roi_percentage = self.calculate_roi_percentage(current_passengers)
        is_profitable = self.is_profitable(current_passengers)
        
        return {
            'breakeven_passengers': breakeven_passengers,
            'current_profit': current_profit,
            'profit_at_capacity': profit_at_capacity,
            'roi_percentage': roi_percentage,
            'is_profitable': is_profitable,
            'total_fixed_costs': self.total_fixed_costs,
            'contribution_margin_per_person': self.contribution_margin_per_person,
            'net_revenue_per_person': self.net_revenue_per_person,
            'commission_amount_per_person': self.commission_amount_per_person,
            'passengers_needed_for_breakeven': max(0, (breakeven_passengers or 0) - current_passengers),
            'excess_passengers': max(0, current_passengers - (breakeven_passengers or 0)),
        }
    
    def get_cost_breakdown(self, current_passengers: int) -> Dict:
        """
        Get detailed cost breakdown
        
        Args:
            current_passengers: Current number of passengers booked
            
        Returns:
            Dictionary with cost breakdown
        """
        variable_costs_total = self.variable_costs_per_person * current_passengers
        total_costs = self.total_fixed_costs + variable_costs_total
        
        return {
            'fixed_costs': self.fixed_costs,
            'marketing_costs': self.marketing_costs,
            'variable_costs_per_person': self.variable_costs_per_person,
            'variable_costs_total': variable_costs_total,
            'total_costs': total_costs,
            'total_fixed_costs': self.total_fixed_costs,
        }


def analyze_departure_breakeven(departure_data: Dict) -> Dict:
    """
    Convenience function to analyze breakeven for a departure
    
    Args:
        departure_data: Dictionary with departure cost and pricing data
        
    Returns:
        Dictionary with breakeven analysis results
    """
    analyzer = BreakevenAnalyzer(
        fixed_costs=Decimal(str(departure_data.get('fixed_costs', 0))),
        variable_costs_per_person=Decimal(str(departure_data.get('variable_costs_per_person', 0))),
        marketing_costs=Decimal(str(departure_data.get('marketing_costs', 0))),
        price_per_person=Decimal(str(departure_data.get('price_per_person', 0))),
        commission_rate=Decimal(str(departure_data.get('commission_rate', 0))),
        max_capacity=departure_data.get('max_capacity', 0)
    )
    
    current_passengers = departure_data.get('current_passengers', 0)
    
    return {
        'breakeven_analysis': analyzer.get_breakeven_analysis(current_passengers),
        'cost_breakdown': analyzer.get_cost_breakdown(current_passengers),
        'analyzer': analyzer
    }


# Example usage and testing
if __name__ == "__main__":
    # Example: Test breakeven analysis
    test_data = {
        'fixed_costs': 300.00,
        'variable_costs_per_person': 20.00,
        'marketing_costs': 10.00,
        'price_per_person': 1000.00,
        'commission_rate': 9.96,
        'max_capacity': 12,
        'current_passengers': 8
    }
    
    results = analyze_departure_breakeven(test_data)
    
    print("=== Breakeven Analysis Results ===")
    print(f"Breakeven Passengers: {results['breakeven_analysis']['breakeven_passengers']}")
    print(f"Current Profit: ${results['breakeven_analysis']['current_profit']}")
    print(f"ROI: {results['breakeven_analysis']['roi_percentage']:.1f}%")
    print(f"Is Profitable: {results['breakeven_analysis']['is_profitable']}")
    
    print("\n=== Cost Breakdown ===")
    print(f"Total Costs: ${results['cost_breakdown']['total_costs']}")
    print(f"Fixed Costs: ${results['cost_breakdown']['fixed_costs']}")
    print(f"Variable Costs: ${results['cost_breakdown']['variable_costs_total']}")
    print(f"Marketing Costs: ${results['cost_breakdown']['marketing_costs']}")

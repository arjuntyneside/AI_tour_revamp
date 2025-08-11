from django.core.management.base import BaseCommand
from core.breakeven_analysis import BreakevenAnalyzer, analyze_departure_breakeven
from decimal import Decimal

class Command(BaseCommand):
    help = 'Test the breakeven analysis module'

    def handle(self, *args, **options):
        self.stdout.write("Testing Breakeven Analysis Module...")
        
        # Test case 1: Profitable scenario
        self.stdout.write("\n=== Test Case 1: Profitable Scenario ===")
        test_data_1 = {
            'fixed_costs': 300.00,
            'variable_costs_per_person': 20.00,
            'marketing_costs': 10.00,
            'price_per_person': 1000.00,
            'commission_rate': 9.96,
            'max_capacity': 12,
            'current_passengers': 8
        }
        
        results_1 = analyze_departure_breakeven(test_data_1)
        analysis_1 = results_1['breakeven_analysis']
        costs_1 = results_1['cost_breakdown']
        
        self.stdout.write(f"Breakeven Passengers: {analysis_1['breakeven_passengers']}")
        self.stdout.write(f"Current Profit: ${analysis_1['current_profit']}")
        self.stdout.write(f"ROI: {analysis_1['roi_percentage']:.1f}%")
        self.stdout.write(f"Is Profitable: {analysis_1['is_profitable']}")
        self.stdout.write(f"Total Costs: ${costs_1['total_costs']}")
        self.stdout.write(f"Contribution Margin per Person: ${analysis_1['contribution_margin_per_person']}")
        
        # Test case 2: Below breakeven scenario
        self.stdout.write("\n=== Test Case 2: Below Breakeven Scenario ===")
        test_data_2 = {
            'fixed_costs': 500.00,
            'variable_costs_per_person': 50.00,
            'marketing_costs': 100.00,
            'price_per_person': 200.00,
            'commission_rate': 10.00,
            'max_capacity': 15,
            'current_passengers': 3
        }
        
        results_2 = analyze_departure_breakeven(test_data_2)
        analysis_2 = results_2['breakeven_analysis']
        
        self.stdout.write(f"Breakeven Passengers: {analysis_2['breakeven_passengers']}")
        self.stdout.write(f"Current Profit: ${analysis_2['current_profit']}")
        self.stdout.write(f"ROI: {analysis_2['roi_percentage']:.1f}%")
        self.stdout.write(f"Is Profitable: {analysis_2['is_profitable']}")
        self.stdout.write(f"Passengers Needed: {analysis_2['passengers_needed_for_breakeven']}")
        
        # Test case 3: Edge case - no profit possible
        self.stdout.write("\n=== Test Case 3: No Profit Possible ===")
        test_data_3 = {
            'fixed_costs': 1000.00,
            'variable_costs_per_person': 150.00,
            'marketing_costs': 200.00,
            'price_per_person': 100.00,  # Price too low
            'commission_rate': 5.00,
            'max_capacity': 10,
            'current_passengers': 5
        }
        
        results_3 = analyze_departure_breakeven(test_data_3)
        analysis_3 = results_3['breakeven_analysis']
        
        self.stdout.write(f"Breakeven Passengers: {analysis_3['breakeven_passengers']}")
        self.stdout.write(f"Current Profit: ${analysis_3['current_profit']}")
        self.stdout.write(f"ROI: {analysis_3['roi_percentage']:.1f}%")
        self.stdout.write(f"Is Profitable: {analysis_3['is_profitable']}")
        
        self.stdout.write(
            self.style.SUCCESS(
                "\n✅ Breakeven analysis module tested successfully!"
            )
        )

from django.core.management.base import BaseCommand
from core.models import TourDeparture
from core.breakeven_analysis import BreakevenAnalyzer

class Command(BaseCommand):
    help = 'Recalculate breakeven values using the new breakeven analysis module'

    def handle(self, *args, **options):
        departures = TourDeparture.objects.all()
        updated_count = 0
        
        self.stdout.write(f"Found {departures.count()} departures to process...")
        
        for departure in departures:
            try:
                # Store original values for comparison
                original_breakeven = departure.breakeven_passengers
                original_profit = departure.profit_at_capacity
                original_roi = departure.roi_percentage
                
                # Create breakeven analyzer
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
                
                # Update departure fields
                departure.breakeven_passengers = analysis['breakeven_passengers']
                departure.profit_at_capacity = analysis['profit_at_capacity']
                departure.roi_percentage = analysis['roi_percentage']
                
                # Check if values changed
                if (departure.breakeven_passengers != original_breakeven or 
                    departure.profit_at_capacity != original_profit or 
                    departure.roi_percentage != original_roi):
                    
                    self.stdout.write(
                        f"Updated departure {departure.id}: "
                        f"Breakeven: {original_breakeven} → {departure.breakeven_passengers}, "
                        f"Profit: {original_profit} → {departure.profit_at_capacity}, "
                        f"ROI: {original_roi} → {departure.roi_percentage}"
                    )
                    updated_count += 1
                
                # Save the departure
                departure.save()
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error processing departure {departure.id}: {str(e)}"
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed {departures.count()} departures. "
                f"Updated {updated_count} breakeven values."
            )
        )

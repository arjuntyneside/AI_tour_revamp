// Departure Form-specific JavaScript extracted from departure_form.html
// Real-time financial calculation
function calculateFinancials() {
    // Get form field IDs from window object
    const fieldIds = window.departureFormData?.fieldIds || {};
    const totalCapacity = window.departureFormData?.totalCapacity || 0;
    
    const pricePerPerson = parseFloat(document.getElementById(fieldIds.current_price_per_person)?.value) || 0;
    const fixedCosts = parseFloat(document.getElementById(fieldIds.fixed_costs)?.value) || 0;
    const variableCostsPerPerson = parseFloat(document.getElementById(fieldIds.variable_costs_per_person)?.value) || 0;
    const marketingCosts = parseFloat(document.getElementById(fieldIds.marketing_costs)?.value) || 0;
    const commissionRate = parseFloat(document.getElementById(fieldIds.commission_rate)?.value) || 0;
    const totalBookings = parseInt(document.getElementById(fieldIds.total_bookings)?.value) || 0;
    
    // Calculate financial metrics
    const totalFixedCosts = fixedCosts + marketingCosts;
    const commissionAmount = (pricePerPerson * commissionRate) / 100;
    const netRevenuePerPerson = pricePerPerson - commissionAmount;
    const contributionMarginPerPerson = netRevenuePerPerson - variableCostsPerPerson;
    
    // Breakeven calculation
    let breakevenPassengers = 'N/A';
    if (contributionMarginPerPerson > 0) {
        breakevenPassengers = Math.ceil(totalFixedCosts / contributionMarginPerPerson);
    }
    
    // Profit at capacity
    let profitAtCapacity = '$0.00';
    if (breakevenPassengers !== 'N/A' && totalCapacity > breakevenPassengers) {
        const excessPassengers = totalCapacity - breakevenPassengers;
        const profit = excessPassengers * contributionMarginPerPerson;
        profitAtCapacity = `$${profit.toFixed(2)}`;
    }
    
    // ROI calculation
    let roiPercentage = '0%';
    const totalInvestment = totalFixedCosts + (totalCapacity * variableCostsPerPerson);
    if (totalInvestment > 0 && profitAtCapacity !== '$0.00') {
        const profit = parseFloat(profitAtCapacity.replace('$', ''));
        const roi = (profit / totalInvestment) * 100;
        roiPercentage = `${roi.toFixed(1)}%`;
    }
    
    // Calculate remaining spots
    const remainingSpots = totalCapacity - totalBookings;
    const spotsLeftElement = document.getElementById('spots-left');
    if (spotsLeftElement) {
        spotsLeftElement.textContent = remainingSpots;
    }
    
    // Update display
    const breakevenElement = document.getElementById('breakeven-passengers');
    const contributionElement = document.getElementById('contribution-margin');
    const profitElement = document.getElementById('profit-at-capacity');
    const roiElement = document.getElementById('roi-percentage');
    
    if (breakevenElement) breakevenElement.textContent = breakevenPassengers;
    if (contributionElement) contributionElement.textContent = `$${contributionMarginPerPerson.toFixed(2)}`;
    if (profitElement) profitElement.textContent = profitAtCapacity;
    if (roiElement) roiElement.textContent = roiPercentage;
}

// Add event listeners to form fields
document.addEventListener('DOMContentLoaded', function() {
    const fieldIds = window.departureFormData?.fieldIds || {};
    
    const financialFields = [
        fieldIds.current_price_per_person,
        fieldIds.fixed_costs,
        fieldIds.variable_costs_per_person,
        fieldIds.marketing_costs,
        fieldIds.commission_rate,
        fieldIds.total_bookings
    ];
    
    financialFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', calculateFinancials);
        }
    });
    
    // Calculate initial values
    calculateFinancials();
});

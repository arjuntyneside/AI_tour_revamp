// Dashboard-specific JavaScript extracted from dashboard.html
// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing chart...');
    
    // Debug: Check if we have data
    let monthsData = window.dashboardData?.monthsData || [];
    let revenueData = window.dashboardData?.revenueData || [];
    let profitData = window.dashboardData?.profitData || [];
    let costData = window.dashboardData?.costData || [];

    console.log('Months data:', monthsData);
    console.log('Revenue data:', revenueData);
    console.log('Profit data:', profitData);
    console.log('Cost data:', costData);

    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.error('Chart.js is not loaded!');
        document.getElementById('no-data-message').innerHTML = '<p>Chart library not loaded. Please refresh the page.</p>';
        document.getElementById('no-data-message').style.display = 'block';
        document.getElementById('financialChart').style.display = 'none';
        return;
    } else {
        console.log('Chart.js is loaded successfully');
    }

    // Check if we have any data
    let hasData = monthsData.length > 0 && (revenueData.some(r => r > 0) || profitData.some(p => p > 0) || costData.some(c => c > 0));

    if (!hasData) {
        // Use sample data for demonstration
        console.log('No real data, using sample data for demonstration');
        monthsData = ['Jan 2024', 'Feb 2024', 'Mar 2024', 'Apr 2024', 'May 2024', 'Jun 2024'];
        revenueData = [12000, 15000, 18000, 14000, 22000, 25000];
        profitData = [3000, 4000, 5000, 2000, 7000, 8000];
        costData = [9000, 11000, 13000, 12000, 15000, 17000];
        hasData = true;
    }

    // Financial Performance Chart
    const ctx = document.getElementById('financialChart');
    if (!ctx) {
        console.error('Canvas element not found!');
        return;
    } else {
        console.log('Canvas found, creating chart...');
        const chartCtx = ctx.getContext('2d');

        console.log('Creating chart with data:', { monthsData, revenueData, profitData, costData });
        
        try {
            const financialChart = new Chart(chartCtx, {
                type: 'line',
                data: {
                    labels: monthsData,
                    datasets: [
                        {
                            label: 'Revenue',
                            data: revenueData,
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'Profit',
                            data: profitData,
                            borderColor: '#3b82f6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'Costs',
                            data: costData,
                            borderColor: '#ef4444',
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20,
                                font: {
                                    size: 12,
                                    weight: '600'
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    elements: {
                        point: {
                            radius: 6,
                            hoverRadius: 8
                        }
                    }
                }
            });
            console.log('Chart created successfully!');
        } catch (error) {
            console.error('Error creating chart:', error);
            document.getElementById('no-data-message').innerHTML = '<p>Error creating chart: ' + error.message + '</p>';
            document.getElementById('no-data-message').style.display = 'block';
            document.getElementById('financialChart').style.display = 'none';
        }
    }
});
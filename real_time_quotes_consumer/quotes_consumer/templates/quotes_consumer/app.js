document.addEventListener("DOMContentLoaded", function() {
    const portfolioId = 1; // Replace with the actual portfolio ID you want to query

    // Fetch risk exposure and factor contribution data
    fetch(`/api/risk-exposure/?portfolio_id=${portfolioId}`)
        .then(response => response.json())
        .then(data => {
            renderHeatmap(data.risk_exposure);
            renderFactorAnalysisChart(data.factor_contributions);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
});

function renderHeatmap(riskExposures) {
    const zData = [];
    const xData = [];
    const yData = [];

    // Process data for the heatmap
    riskExposures.forEach(item => {
        xData.push(item.risk_factor.name);
        yData.push(item.portfolio_id);
        zData.push(item.exposure_value);
    });

    const trace = {
        z: [zData],
        x: xData,
        y: yData,
        type: 'heatmap'
    };

    const layout = {
        title: 'Risk Exposure Heatmap',
        xaxis: { title: 'Risk Factors' },
        yaxis: { title: 'Portfolio' }
    };

    Plotly.newPlot('heatmap', [trace], layout);
}

function renderFactorAnalysisChart(factorContributions) {
    const labels = [];
    const dataPoints = [];

    // Process data for the factor analysis chart
    factorContributions.forEach(item => {
        labels.push(item.risk_factor.name);
        dataPoints.push(item.contribution_value);
    });

    const ctx = document.getElementById('factorAnalysisChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Contribution to Total Risk',
                data: dataPoints,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            title: {
                display: true,
                text: 'Factor Analysis'
            },
            scales: {
                yAxes: [{
                    ticks: {
                        beginAtZero: true
                    }
                }]
            }
        }
    });
}

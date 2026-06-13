document.addEventListener('DOMContentLoaded', () => {
    const chartElement = document.getElementById('chart');

    if (!chartElement) {
        console.error('Canvas element not found.');
        return;
    }

    const ctx = chartElement.getContext('2d');

    const gradient = ctx.createLinearGradient(0, 0, 0, 100);
    gradient.addColorStop(0, '#ff6b00');
    gradient.addColorStop(1, '#ff9500');

    const forecastItems = document.querySelectorAll('.forecast-item');

    const temps = [];
    const dates = [];

    forecastItems.forEach(item => {
    const date = item.querySelector('.forecast-time')?.textContent.trim();
    const temp = item.querySelector('.forecast-temperatureValue')?.textContent.trim();
    const hum = item.querySelector('.forecast-humidityValue')?.textContent.trim();

    if (date && temp) {
        dates.push(date);
        temps.push(parseFloat(temp));
    }
});

    if (temps.length === 0 || dates.length === 0) {
        console.error('Temperature or date values are missing.');
        return;
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                data: temps,
                borderColor: gradient,
                borderWidth: 3,
                tension: 0.5,
                pointRadius: 4,
                pointHoverRadius: 6,
                fill: false
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    display: false,
                    grid: {
                        display: false
                    }
                },
                y: {
                    display: false,
                    grid: {
                        display: false
                    },
                    min: Math.min(...temps) - 3,
                    max: Math.max(...temps) + 3
                }
            }
        }
    });
});
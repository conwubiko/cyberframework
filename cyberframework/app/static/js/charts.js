/* CROF Chart.js Utilities */

const CROF_COLORS = {
    accent: '#00BCD4',
    accentAlpha: 'rgba(0, 188, 212, 0.2)',
    success: '#2ea043',
    warning: '#d29922',
    danger: '#f85149',
    info: '#58a6ff',
    gridColor: 'rgba(139, 148, 158, 0.15)',
    textColor: '#8b949e',
};

const FUNCTION_COLORS = [
    '#00BCD4', '#58a6ff', '#2ea043', '#d29922',
    '#f85149', '#bc8cff', '#f778ba', '#ffa657'
];

Chart.defaults.color = CROF_COLORS.textColor;
Chart.defaults.borderColor = CROF_COLORS.gridColor;

function createRadarChart(canvasId, labels, scores) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score %',
                data: scores,
                backgroundColor: CROF_COLORS.accentAlpha,
                borderColor: CROF_COLORS.accent,
                borderWidth: 2,
                pointBackgroundColor: CROF_COLORS.accent,
                pointBorderColor: '#fff',
                pointRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        color: CROF_COLORS.textColor,
                        backdropColor: 'transparent',
                    },
                    grid: { color: CROF_COLORS.gridColor },
                    angleLines: { color: CROF_COLORS.gridColor },
                    pointLabels: {
                        color: CROF_COLORS.textColor,
                        font: { size: 12, weight: 'bold' }
                    }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function createBarChart(canvasId, labels, scores) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const colors = labels.map((_, i) => FUNCTION_COLORS[i % FUNCTION_COLORS.length]);
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score %',
                data: scores,
                backgroundColor: colors.map(c => c + '99'),
                borderColor: colors,
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: CROF_COLORS.gridColor },
                    ticks: { color: CROF_COLORS.textColor }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: CROF_COLORS.textColor }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

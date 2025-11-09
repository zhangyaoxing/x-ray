var bar_labels = [];
var count = [];
var total_slow_ms = [];
data.forEach(d => {
    bar_labels.push(d.time);
    count.push(d.count);
    total_slow_ms.push(d.total_slow_ms);
});

const ctx = document.getElementById('canvas_{name}').getContext('2d');
chart1 = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: bar_labels,
        datasets: [
            {
                label: 'Slow Count',
                data: count,
                type: 'bar',
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                yAxisID: 'y'
            },
            {
                label: 'Total Slow (ms)',
                data: total_slow_ms,
                type: 'line',
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                fill: false,
                yAxisID: 'y1',
                tension: 0.3,
                pointRadius: 2
            }
        ]
    },
    options: {
        responsive: true,
        animation: {
            duration: ANIMATION_DURATION
        },
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    usePointStyle: true,
                    generateLabels: genDefaultLegendLabels
                }
            },
            zoom: ZOOM_OPTIONS
        },
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: 'Count' }
            },
            y1: {
                beginAtZero: true,
                position: 'right',
                title: { display: true, text: 'Total Slow (ms)' },
                grid: { drawOnChartArea: false }
            }
        }
    }
});
charts.push(chart1);

var nsCount = {};
data.forEach(d => {
    Object.entries(d.byNs).forEach(([ns, val]) => {
        nsCount[ns] = (nsCount[ns] || 0) + (val.count || 0);
    });
});

var labels = Object.keys(nsCount);
var dataSlow = Object.values(nsCount);
var colors = labels.map((_, i) => `hsl(${i * 360 / labels.length}, 70%, 60%)`);

const ctx_byns = document.getElementById('canvas_{name}_byns').getContext('2d');
var chart2 = new Chart(ctx_byns, {
    type: 'pie',
    data: {
        labels: labels,
        datasets: [{
            data: dataSlow,
            backgroundColor: colors
        }]
    },
    options: {
        plugins: {
            title: {
                display: true,
                text: 'Slow Count by Namespace'
            },
            legend: {
                position: 'right',
                labels: {
                    usePointStyle: true,
                    pointStyle: 'rect'
                }
            }
        }
    }
});
charts.push(chart2);

var nsSlowMs = {};
data.forEach(d => {
    Object.entries(d.byNs).forEach(([ns, val]) => {
        nsSlowMs[ns] = (nsSlowMs[ns] || 0) + (val.total_slow_ms || 0);
    });
});

var dataSlow = Object.values(nsSlowMs);
const ctx_byns_ms = document.getElementById('canvas_{name}_byns_ms').getContext('2d');
var chart3 = new Chart(ctx_byns_ms, {
    type: 'pie',
    data: {
        labels: labels,
        datasets: [{
            data: dataSlow,
            backgroundColor: colors
        }]
    },
    options: {
        plugins: {
            title: {
                display: true,
                text: 'Slow MS by Namespace'
            },
            legend: {
                position: 'right',
                labels: {
                    usePointStyle: true,
                    pointStyle: 'rect'
                }
            }
        }
    }
});
charts.push(chart3);
resetButton.onclick = function () {
    chart1.resetZoom();
}
var labels = [];
var created = [];
var ended = [];
var total = [];
data.forEach(d => {
    labels.push(d.time);
    created.push(d.created);
    ended.push(-d.ended);
    total.push(d.total);
});

const ctx = document.getElementById('canvas_{name}').getContext('2d');
var chart1 = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: labels,
        datasets: [
            {
                label: 'Connections Created',
                data: created,
                type: 'bar',
                stack: 'Stack 0',
                backgroundColor: 'rgba(54, 162, 235, 0.7)'
            },
            {
                label: 'Connections Ended',
                data: ended,
                type: 'bar',
                stack: 'Stack 0',
                backgroundColor: 'rgba(255, 99, 132, 0.7)'
            },
            {
                label: 'Total Connections',
                data: total,
                type: 'line',
                borderColor: 'rgba(255, 206, 86, 1)',
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
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
            title: {
                display: true,
                text: 'Connection Create/Ended Rate Over Time'
            },
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
                title: { display: true, text: 'Connections per minute' }
            },
            y1: {
                beginAtZero: true,
                position: 'right',
                title: { display: true, text: 'Total Connections' },
                grid: { drawOnChartArea: false }
            }
        }
    }
});
charts.push(chart1);

var labels = data.map(d => d.time);
var ipSet = new Set();
data.forEach(d => Object.keys(d.byIp).forEach(ip => ipSet.add(ip)));
const ips = Array.from(ipSet);

const datasets_byip = [];
ips.forEach(ip => {
    // created
    datasets_byip.push({
        label: ip + ' created',
        data: data.map(d => d.byIp[ip]?.created || 0),
        stack: "Stack 0"
    });
    // ended
    datasets_byip.push({
        label: ip + ' ended',
        data: data.map(d => -(d.byIp[ip]?.ended || 0)),
        stack: "Stack 0"
    });
});

const ctx_byip = document.getElementById('canvas_{name}_byip').getContext('2d');
const displayLegend = datasets_byip.length <= MAX_LEGENDS;
var chart2 = new Chart(ctx_byip, {
    type: 'bar',
    data: {
        labels: labels,
        datasets: datasets_byip.map(ds => ({
            label: ds.label,
            data: ds.data,
            type: 'bar',
            stack: ds.stack
        }))
    },
    options: {
        plugins: {
            title: {
                display: true,
                text: 'Connections Created/Ended by IP Over Time'
            },
            legend: {
                position: 'top',
                display: displayLegend,
                labels: {
                    usePointStyle: true,
                    generateLabels: genDefaultLegendLabels
                }
            },
            zoom: ZOOM_OPTIONS
        },
        responsive: true,
        animation: {
            duration: ANIMATION_DURATION
        },
        scales: {
            x: { stacked: true },
            y: {
                stacked: true,
                beginAtZero: true,
                title: { display: true, text: 'Connections' }
            }
        }
    }
});
charts.push(chart2);

resetButton.onclick = function () {
    chart1.resetZoom();
    chart2.resetZoom();
}
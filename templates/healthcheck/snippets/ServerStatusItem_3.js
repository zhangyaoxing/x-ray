const labels = Object.keys(data);
const operations = ['insert', 'query', 'update', 'delete', 'command', 'getmore'];
const colors = [
    'rgba(255, 99, 132, 0.8)',
    'rgba(54, 162, 235, 0.8)',
    'rgba(255, 206, 86, 0.8)',
    'rgba(75, 192, 192, 0.8)',
    'rgba(153, 102, 255, 0.8)',
    'rgba(255, 159, 64, 0.8)'
];

const datasets = operations.map((op, index) => ({
    label: op.charAt(0).toUpperCase() + op.slice(1),
    data: labels.map(key => data[key][op]),
    backgroundColor: colors[index]
}));

let wrapper = document.createElement('div');
let canvas = document.createElement('canvas');
wrapper.className = "bar";
canvas.className = 'bar';
container.appendChild(wrapper);
wrapper.appendChild(canvas);
const ctx = canvas.getContext('2d');

const chart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: labels,
        datasets: datasets
    },
    options: {
        responsive: true,
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Server'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Operation Count'
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'Operations by Server'
            },
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                mode: 'point',
                intersect: true
            }
        }
    }
});
charts.push(chart);

const namespaces = [...new Set(data.map(item => item.ns))];
const labels = [...new Set(data.map(item => item.label))];

const latencyTypes = [
    { key: 'readsLatency', name: 'Reads', color: [54, 162, 235] },
    { key: 'writesLatency', name: 'Writes', color: [255, 99, 132] },
    { key: 'commandsLatency', name: 'Commands', color: [255, 206, 86] },
    { key: 'transactionsLatency', name: 'Transactions', color: [75, 192, 192] }
];

const datasets = [];

labels.forEach((label, labelIndex) => {
    latencyTypes.forEach((type, typeIndex) => {
        const latencyData = namespaces.map(ns => {
            const item = data.find(d => d.ns === ns && d.label === label);
            return item ? item[type.key] : 0;
        });

        datasets.push({
            label: `${label} - ${type.name}`,
            data: latencyData,
            backgroundColor: `rgba(${type.color[0]}, ${type.color[1]}, ${type.color[2]}, ${0.8 - labelIndex * 0.15})`,
            stack: 'stack' + labelIndex
        });
    });
});

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
        labels: namespaces,
        datasets: datasets
    },
    options: {
        indexAxis: 'y',
        scales: {
            x: {
                stacked: true,
                title: {
                    display: true,
                    text: 'Latency (ms)'
                }
            },
            y: {
                stacked: true,
                title: {
                    display: true,
                    text: 'Namespace'
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'Operation Latency by Namespace'
            },
            legend: {
                display: true,
                position: 'right'
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const label = context.dataset.label || '';
                        const value = (context.parsed.x || 0).toFixed(2);
                        return label + ': ' + value + ' ms';
                    }
                }
            }
        }
    }
});
charts.push(chart);

const labels = Object.keys(data);
const currentData = labels.map(key => data[key].current);
const availableData = labels.map(key => data[key].available);
const activeData = labels.map(key => data[key].active);
const threadedData = labels.map(key => data[key].threaded);
const totalCreatedData = labels.map(key => data[key].totalCreated);

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
        datasets: [
            {
                label: 'Current',
                data: currentData,
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                stack: 'stack1',
                yAxisID: 'y',
                availableData: availableData
            },
            {
                label: 'Active',
                data: activeData,
                backgroundColor: 'rgba(255, 206, 86, 0.8)',
                stack: 'stack2',
                yAxisID: 'y'
            },
            {
                label: 'Threaded',
                data: threadedData,
                backgroundColor: 'rgba(153, 102, 255, 0.8)',
                stack: 'stack3',
                yAxisID: 'y'
            },
            {
                label: 'Total Created',
                data: totalCreatedData,
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                stack: 'stack4',
                yAxisID: 'y1'
            }
        ]
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
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: 'Connection Count'
                },
                stacked: true
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: 'Total Created'
                },
                grid: {
                    drawOnChartArea: false
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'Connection Statistics by Server'
            },
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                mode: 'point',
                intersect: true,
                callbacks: {
                    label: function (context) {
                        const label = context.dataset.label || '';
                        const value = context.parsed.y;
                        if (label === 'Current' && context.dataset.availableData) {
                            const available = context.dataset.availableData[context.dataIndex];
                            return [
                                label + ': ' + value,
                                'Available: ' + available
                            ];
                        }

                        return label + ': ' + value;
                    }
                }
            }
        }
    }
});
charts.push(chart);

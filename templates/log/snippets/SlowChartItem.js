const groupedDataDuration = {};
const groupedDataScanned = {};
const groupedDataScannedObj = {};
const positioner = document.getElementById('positioner_{name}');
const code = positioner.nextElementSibling.getElementsByTagName('code')[0];
data.forEach((item, i) => {
    const namespace = item.attr.ns || '(unknown)';
    if (!groupedDataDuration[namespace]) {
        groupedDataDuration[namespace] = [];
        groupedDataScanned[namespace] = [];
        groupedDataScannedObj[namespace] = [];
    }
    
    const timestamp = new Date(item.t);
    groupedDataDuration[namespace].push({
        index: i,
        x: timestamp.getTime(),
        y: item.attr.durationMillis,
        timeLabel: timestamp.toLocaleTimeString()
    });
    groupedDataScanned[namespace].push({
        index: i,
        x: timestamp.getTime(),
        y: item.attr.keysExamined || 0,
        timeLabel: timestamp.toLocaleTimeString()
    });
    groupedDataScannedObj[namespace].push({
        index: i,
        x: timestamp.getTime(),
        y: item.attr.docsExamined || 0,
        timeLabel: timestamp.toLocaleTimeString()
    })
});

const dssDuration = Object.keys(groupedDataDuration).map((namespace) => {
    const backgroundColor = generateRandomColor(0.8);
    const borderColor = generateRandomColor(1);
    
    return {
        label: namespace,
        data: groupedDataDuration[namespace],
        backgroundColor: backgroundColor,
        borderColor: borderColor,
        borderWidth: 1,
        pointRadius: 4
    };
});

const dssScanned = Object.keys(groupedDataScanned).map((namespace) => {
    const backgroundColor = generateRandomColor(0.8);
    const borderColor = generateRandomColor(1);
    
    return {
        label: namespace,
        data: groupedDataScanned[namespace],
        backgroundColor: backgroundColor,
        borderColor: borderColor,
        borderWidth: 1,
        pointRadius: 4
    };
});

const dssScannedObj = Object.keys(groupedDataScannedObj).map((namespace) => {
    const backgroundColor = generateRandomColor(0.8);
    const borderColor = generateRandomColor(1);

    return {
        label: namespace,
        data: groupedDataScannedObj[namespace],
        backgroundColor: backgroundColor,
        borderColor: borderColor,
        borderWidth: 1,
        pointRadius: 4
    };
});

highlighted = -1;
function onClick(event, activeElements) {
    if (activeElements.length > 0) {
        const datasetIndex = activeElements[0].datasetIndex;
        const dataIndex = activeElements[0].index;
        const dataset = this.data.datasets[datasetIndex];
        const dataPoint = dataset.data[dataIndex];
        const originalData = data[dataPoint.index];
        
        if (highlighted === dataPoint.index) {
            code.textContent = '// Click data points to review original log line...';
            highlighted = -1;
        } else {
            code.textContent = JSON.stringify(originalData, null, 2);
            highlighted = dataPoint.index;
        }
        delete code.dataset.highlighted;
        hljs.highlightElement(code);
    }
}
const configDuration = {
    type: 'scatter',
    data: {
        datasets: dssDuration
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Slow Operations - Duration vs Time by Namespace'
            },
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                callbacks: {
                    title: function(context) {
                        const point = context[0].raw;
                        return new Date(point.x).toLocaleString();
                    },
                    label: function(context) {
                        const point = context.raw;
                        return [
                            `Namespace: ${context.dataset.label}`,
                            `Duration: ${point.y}ms`,
                            `Time: ${new Date(point.x).toLocaleString()}`
                        ];
                    }
                }
            }
        },
        scales: {
            x: {
                type: 'linear',
                position: 'bottom',
                title: {
                    display: true,
                    text: 'Time'
                },
                ticks: {
                    callback: function(t) {
                        return new Date(t).toLocaleTimeString();
                    },
                    maxTicksLimit: 10
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Duration (milliseconds)'
                },
                beginAtZero: true
            }
        },
        interaction: {
            mode: 'point',
            intersect: false
        },
        onClick: onClick
    }
};
const configScanned = {
    type: 'scatter',
    data: {
        datasets: dssScanned
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Slow Operations - Scanned vs Time by Namespace'
            },
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                callbacks: {
                    title: function(context) {
                        const point = context[0].raw;
                        return new Date(point.x).toLocaleString();
                    },
                    label: function(context) {
                        const point = context.raw;
                        return [
                            `Namespace: ${context.dataset.label}`,
                            `Scanned: ${point.y}`,
                            `Time: ${new Date(point.x).toLocaleString()}`
                        ];
                    }
                }
            }
        },
        scales: {
            x: {
                type: 'linear',
                position: 'bottom',
                title: {
                    display: true,
                    text: 'Time'
                },
                ticks: {
                    callback: function(t) {
                        return new Date(t).toLocaleTimeString();
                    },
                    maxTicksLimit: 10
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Scanned Keys'
                },
                beginAtZero: true
            }
        },
        interaction: {
            mode: 'point',
            intersect: false
        },
        onClick: onClick
    }
};

const configScannedObj = {
    type: 'scatter',
    data: {
        datasets: dssScannedObj
    },
    options: {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: 'Slow Operations - Scanned Objects vs Time by Namespace'
            },
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                callbacks: {
                    title: function(context) {
                        const point = context[0].raw;
                        return new Date(point.x).toLocaleString();
                    },
                    label: function(context) {
                        const point = context.raw;
                        return [
                            `Namespace: ${context.dataset.label}`,
                            `Scanned Obj: ${point.y}`,
                            `Time: ${new Date(point.x).toLocaleString()}`
                        ];
                    }
                }
            }
        },
        scales: {
            x: {
                type: 'linear',
                position: 'bottom',
                title: {
                    display: true,
                    text: 'Time'
                },
                ticks: {
                    callback: function(t) {
                        return new Date(t).toLocaleTimeString();
                    },
                    maxTicksLimit: 10
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Scanned Objects'
                },
                beginAtZero: true
            }
        },
        interaction: {
            mode: 'point',
            intersect: false
        },
        onClick: onClick
    }
};

const ctx1 = document.getElementById('canvas_{name}_duration').getContext('2d');
const chart1 = new Chart(ctx1, configDuration);
charts.push(chart1);

const ctx2 = document.getElementById('canvas_{name}_scanned').getContext('2d');
const chart2 = new Chart(ctx2, configScanned);
charts.push(chart2);

const ctx3 = document.getElementById('canvas_{name}_scannedObj').getContext('2d');
const chart3 = new Chart(ctx3, configScannedObj);
charts.push(chart3);
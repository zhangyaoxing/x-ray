const labels = Object.keys(data);
const inCacheSizeData = labels.map(key => data[key].inCacheSize);
const readIntoData = labels.map(key => data[key].readInto);
const writtenFromData = labels.map(key => Math.abs(data[key].writtenFrom));
const forUpdatesData = labels.map(key => data[key].forUpdates);
const dirtyData = labels.map(key => data[key].dirty);
const cacheSizeData = labels.map(key => data[key].cacheSize);

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
                label: 'Bytes In Cache',
                data: inCacheSizeData,
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                yAxisID: 'y',
                cacheSizes: cacheSizeData
            },
            {
                label: 'Bytes Allocated for Updates',
                data: forUpdatesData,
                backgroundColor: 'rgba(255, 206, 86, 0.8)',
                yAxisID: 'y',
                cacheSizes: cacheSizeData
            },
            {
                label: 'Bytes Dirty in Cache',
                data: dirtyData,
                backgroundColor: 'rgba(153, 102, 255, 0.8)',
                yAxisID: 'y',
                cacheSizes: cacheSizeData
            },
            {
                label: 'Bytes Read Into',
                data: readIntoData,
                backgroundColor: 'rgba(75, 192, 192, 0.8)',
                yAxisID: 'y1'
            },
            {
                label: 'Bytes Written From',
                data: writtenFromData,
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
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
                    text: 'Cache Size (Bytes)'
                },
                beginAtZero: true
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: 'I/O (Bytes/sec)'
                },
                grid: {
                    drawOnChartArea: false
                },
                beginAtZero: true
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'WiredTiger Cache Statistics'
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

                        if (label === 'Bytes In Cache' && context.dataset.cacheSizes) {
                            const cacheSize = context.dataset.cacheSizes[context.dataIndex];
                            const fillRatio = ((value / cacheSize) * 100).toFixed(2);
                            return [
                                label + ': ' + formatSize(value),
                                'Cache Fill Ratio: ' + fillRatio + '%'
                            ];
                        }
                        if (label === 'Bytes Allocated for Updates' && context.dataset.cacheSizes) {
                            const cacheSize = context.dataset.cacheSizes[context.dataIndex];
                            const updateRatio = ((value / cacheSize) * 100).toFixed(2);
                            return [
                                label + ': ' + formatSize(value),
                                'Updates Ratio: ' + updateRatio + '%'
                            ];
                        }
                        if (label === 'Bytes Dirty in Cache' && context.dataset.cacheSizes) {
                            const cacheSize = context.dataset.cacheSizes[context.dataIndex];
                            const dirtyRatio = ((value / cacheSize) * 100).toFixed(2);
                            return [
                                label + ': ' + formatSize(value),
                                'Dirty Fill Ratio: ' + dirtyRatio + '%'
                            ];
                        }

                        return label + ': ' + formatSize(value) + '/s';
                    }
                }
            }
        }
    }
});
charts.push(chart);

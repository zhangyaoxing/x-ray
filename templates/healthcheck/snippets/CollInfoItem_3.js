const namespaces = [...new Set(data.map(item => item.ns))];
const labels = [...new Set(data.map(item => item.label))];

const collFragDatasets = labels.map((label, index) => {
    const collFragData = namespaces.map(ns => {
        const item = data.find(d => d.ns === ns && d.label === label);
        return item ? item.collFrag * 100 : 0;
    });

    return {
        label: label,
        data: collFragData,
        backgroundColor: `rgba(${54 + index * 80}, ${162 + index * 30}, ${235 - index * 50}, 0.8)`
    };
});

const indexFragDatasets = labels.map((label, index) => {
    const indexFragData = namespaces.map(ns => {
        const item = data.find(d => d.ns === ns && d.label === label);
        return item ? item.indexFrag * 100 : 0;
    });

    return {
        label: label,
        data: indexFragData,
        backgroundColor: `rgba(${255 - index * 50}, ${99 + index * 40}, ${132 + index * 30}, 0.8)`
    };
});

// Collection Fragmentation Chart
let wrapper1 = document.createElement('div');
let canvas1 = document.createElement('canvas');
wrapper1.className = "bar";
canvas1.className = 'bar';
container.appendChild(wrapper1);
wrapper1.appendChild(canvas1);
const ctx1 = canvas1.getContext('2d');

const chart1 = new Chart(ctx1, {
    type: 'bar',
    data: {
        labels: namespaces,
        datasets: collFragDatasets
    },
    options: {
        indexAxis: 'y',
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Collection Fragmentation (%)'
                },
                max: 100
            },
            y: {
                title: {
                    display: true,
                    text: 'Namespace'
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'Collection Fragmentation by Namespace'
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
                        return label + ': ' + value + '%';
                    }
                }
            }
        }
    }
});
charts.push(chart1);

// Index Fragmentation Chart
let wrapper2 = document.createElement('div');
let canvas2 = document.createElement('canvas');
wrapper2.className = "bar";
canvas2.className = 'bar';
container.appendChild(wrapper2);
wrapper2.appendChild(canvas2);
const ctx2 = canvas2.getContext('2d');

const chart2 = new Chart(ctx2, {
    type: 'bar',
    data: {
        labels: namespaces,
        datasets: indexFragDatasets
    },
    options: {
        indexAxis: 'y',
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Index Fragmentation (%)'
                },
                max: 100
            },
            y: {
                title: {
                    display: true,
                    text: 'Namespace'
                }
            }
        },
        plugins: {
            title: {
                display: true,
                text: 'Index Fragmentation by Namespace'
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
                        return label + ': ' + value + '%';
                    }
                }
            }
        }
    }
});
charts.push(chart2);


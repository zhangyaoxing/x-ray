data = data[0];
let valueHostMapping = {};
let hostValueMapping = {};
const datasets = Object.keys(data).map((host, index) => {
    value = index + 1;
    const points = data[host].map(event => {
        const timestamp = new Date(event.timestamp);
        hostValueMapping[host] = value;
        valueHostMapping[value.toString()] = host;
        return {
            x: timestamp.getTime(),
            y: value,
            timestamp: timestamp,
            event: event.event,
            details: event.details,
            id: event.id
        };
    });
    
    return {
        label: host,
        data: points,
        showLine: true,
        tension: 0,
        borderWidth: 10,
        pointBackgroundColor: "white",
        pointRadius: 5,
        pointBorderWidth: 1,
        pointHoverRadius: 8,
        fill: false
    };
});

const canvas = document.getElementById('canvas_{name}')
const height = Object.keys(data).length * 30;
canvas.style.height = `${height}px`;
canvas.height = height;
const ctx = canvas.getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: datasets
    },
    options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            x: {
                type: 'linear',
                title: {
                    display: true,
                    text: 'Time',
                    font: {
                        size: 14,
                        weight: 'bold'
                    }
                },
                ticks: {
                    callback: function(value) {
                        // Convert epoch to ISO time HH:MM:SS
                        const date = new Date(value);
                        const timeStr = date.toISOString().match(/(?<=T)[^\.Z]+/)[0];
                        return timeStr;
                    }
                }
            },
            y: {
                min: 0,
                max: Object.keys(data).length + 1,
                ticks: {
                    stepSize: 1,
                    callback: function(value) {
                        return valueHostMapping[value.toString()] || '';
                    }
                },
                title: {
                    display: true,
                    text: 'Replica Set Members',
                    font: {
                        size: 14,
                        weight: 'bold'
                    }
                }
            }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    title: function(context) {
                        return `${context[0].dataset.label}`;
                    },
                    label: function(context) {
                        const dataPoint = context.raw;
                        const date = dataPoint.timestamp;
                        const timeStr = date.toISOString();
                        const id = dataPoint.id;
                        let detail = "";
                        if (id == 21392) {
                            // config change
                            const v = dataPoint.details.config.version;
                            const t = dataPoint.details.config.term;
                            detail = `{version: ${v}, term: ${t}}`;
                        } else if (id == 21215 || id == 21216) {
                            // new state
                            detail = `${dataPoint.details.new_state}`;
                        } else if (id == 21358) {
                            // state change
                            detail = `${dataPoint.details.from} → ${dataPoint.details.to}`;
                        } else if (id == 4615660) {
                            // priority takeover
                            detail = 'Priority Takeover';
                        }
                        return [
                            `Event: ${dataPoint.event}`,
                            `Log ID: ${dataPoint.id}`,
                            `Time: ${timeStr}`,
                            `Message: ${dataPoint.details.msg || ''}`,
                            `${detail}`
                        ];
                    }
                },
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                titleFont: {
                    size: 14,
                    weight: 'bold'
                },
                bodyFont: {
                    size: 12
                },
                padding: 12,
                displayColors: true
            },
            legend: {
                display: false
            },
            title: {
                display: true,
                text: 'State Transition Timeline',
                font: {
                    size: 16,
                    weight: 'bold'
                },
                padding: 20
            },
            zoom: {
                zoom: {
                    wheel: {
                        enabled: true
                    },
                    pinch: {
                        enabled: true
                    },
                    drag: {
                        enabled: true
                    },
                    mode: 'x'
                },
                pan: {
                    enabled: true,
                    mode: 'x',
                    modifierKey: 'shift'
                },
                limits: {
                    x: {
                        min: "original",
                        max: "original"
                    }
                }
            }
        },
        interaction: {
            mode: 'nearest',
            intersect: true
        }
    }
});
resetButton.onclick = function() {
    chart.resetZoom();
}
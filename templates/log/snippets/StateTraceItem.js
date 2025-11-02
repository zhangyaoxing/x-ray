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
        pointRadius: 6,
        pointHoverRadius: 8,
        showLine: true,
        tension: 0,
        fill: true
    };
});

const ctx = document.getElementById('canvas_{name}').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: datasets
    },
    options: {
        responsive: true,
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
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
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
                },
                grid: {
                    color: 'rgba(0, 0, 0, 0.1)'
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
                        return [
                            `Event: ${dataPoint.event}`,
                            `Log ID: ${dataPoint.id}`,
                            `Time: ${timeStr}`,
                            `Message: ${dataPoint.details.msg || ''}`
                        ];
                    },
                    afterLabel: function(context) {
                        const dataPoint = context.raw;
                        const id = dataPoint.id;
                        if (id == 21392) {
                            const v = dataPoint.details.config.version;
                            const t = dataPoint.details.config.term;
                            return `{version: ${v}, term: ${t}}`;
                        } else if (id == 21215 || id == 21216) {
                            return `${dataPoint.details.new_state}`;
                        } else if (id == 21358) {
                            return `${dataPoint.details.from} → ${dataPoint.details.to}`;
                        } else if (id == 4615660) {
                            return 'Priority Takeover';
                        }
                        return '';
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
                display: true,
                position: 'top',
                labels: {
                    font: {
                        size: 12
                    },
                    padding: 15,
                    usePointStyle: true
                }
            },
            title: {
                display: true,
                text: 'State Transition Timeline',
                font: {
                    size: 16,
                    weight: 'bold'
                },
                padding: 20
            }
        },
        interaction: {
            mode: 'nearest',
            intersect: true
        }
    }
});
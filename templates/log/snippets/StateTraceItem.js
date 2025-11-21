data = data[0] || {};
let valueHostMapping = {};
let hostValueMapping = {};
const COLOR_MAPPING = {
    "STARTUP": 'rgba(102, 29, 248, 0.85)',
    "PRIMARY": 'rgba(54, 197, 22, 0.85)',
    "SECONDARY": 'rgba(249, 224, 0, 0.85)',
    "RECOVERING": 'rgba(255, 159, 64, 0.85)',
    "STARTUP2": 'rgba(153, 102, 255, 0.85)',
    "UNKNOWN": 'rgba(0, 0, 0, 0.85)',
    "ARBITER": 'rgba(51, 182, 247, 0.85)',
    "DOWN": 'rgba(128, 0, 0, 0.85)',
    "ROLLBACK": 'rgba(255, 99, 132, 0.85)',
    "REMOVED": 'rgba(201, 203, 207, 0.85)',
}
const datasets = Object.keys(data).map((host, index) => {
    let value = index + 1;
    // Some events doesn't carry state info, so we need to track the latest state
    let state = "UNKNOWN";
    const points = data[host].map(event => {
        const timestamp = new Date(event.timestamp);
        hostValueMapping[host] = value;
        valueHostMapping[value.toString()] = host;
        let point = {
            x: timestamp.getTime(),
            y: value,
            timestamp: timestamp,
            event: event.event,
            details: event.details,
            id: event.id
        };
        if ([20722, 21215, 21216, 21358].includes(event.id)) {
            // State changed, update the latest state
            state = event.details.new_state || "UNKNOWN";
        }
        point.state = state;
        return point;
    });

    return {
        label: host,
        data: points,
        showLine: true,
        tension: 0,
        borderWidth: 10,
        pointBackgroundColor: FG_COLOR,
        pointBorderColor: FG_COLOR,
        pointBorderWidth: 2,
        pointRadius: 7,
        pointStyle: "line",
        pointRotation: 90,
        pointHoverRadius: 8,
        pointHoverBorderWidth: 4,
        pointHoverBorderColor: 'rgba(0, 255, 255, 0.85)',
        fill: false,
        segment: {
            borderColor: ctx => {
                const state = ctx.p0.raw.state;
                const color = COLOR_MAPPING[state] || 'rgba(0, 0, 0, 1)';
                return color;
            }
        }
    };
});

const canvas = document.getElementById('canvas_{name}')
let height = Object.keys(data).length * 30;
height = height < 90 ? 90 : height;
canvas.style.height = `${height}px`;
canvas.height = height;
const ctx = canvas.getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        datasets: datasets
    },
    options: {
        animation: {
            duration: ANIMATION_DURATION
        },
        responsive: true,
        maintainAspectRatio: true,
        scales: {
            x: {
                type: 'linear',
                title: {
                    display: true,
                    text: 'Time'
                },
                ticks: {
                    callback: function (value) {
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
                    callback: function (value) {
                        return valueHostMapping[value.toString()] || '';
                    }
                },
                title: {
                    display: true,
                    text: 'Replica Set Members',
                }
            }
        },
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    generateLabels: function (chart) {
                        return Object.keys(COLOR_MAPPING).map(state => {
                            return {
                                text: state,
                                fillStyle: COLOR_MAPPING[state],
                                strokeStyle: COLOR_MAPPING[state],
                                lineWidth: 0,
                                fontColor: FG_COLOR,
                                hidden: false,
                            };
                        });
                    },
                    usePointStyle: false, // rectangle style
                    boxWidth: 20,
                    boxHeight: 10,
                    padding: 15,
                }
            },
            tooltip: {
                callbacks: {
                    title: function (context) {
                        return `${context[0].dataset.label}`;
                    },
                    label: function (context) {
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
                            detail = `${dataPoint.details.old_state} → ${dataPoint.details.new_state}`;
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
                padding: 12,
                displayColors: true
            },
            title: {
                display: true,
                text: 'State Transition Timeline',
                padding: 20
            },
            zoom: ZOOM_OPTIONS
        },
        interaction: {
            mode: 'nearest',
            intersect: true
        }
    }
});
resetButton.onclick = function () {
    chart.resetZoom();
}
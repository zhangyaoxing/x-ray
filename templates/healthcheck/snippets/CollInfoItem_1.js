const legendOptions = {
    "display": true,
    "position": "right",
    "labels": {
        "usePointStyle": false,
        "boxWidth": 15,
        "boxHeight": 15
    }
};
const total_size = Object.values(data).reduce((sum, item) => sum + item.size, 0);
const total_index_size = Object.values(data).reduce((sum, item) => sum + item.index_size, 0);
let wrapper = document.createElement('div');
wrapper.className = "pie";
let canvas = document.createElement('canvas');
container.appendChild(wrapper);
wrapper.appendChild(canvas);
const ctx1 = canvas.getContext('2d');

const chart1 = new Chart(ctx1, {
    "type": "pie",
    "data": {
        "labels": Object.keys(data),
        "datasets": [{
            "label": "Size",
            "data": Object.values(data).map(item => item.size)
        }]
    },
    "options": {
        "plugins": {
            "title": {
                "display": true,
                "text": "Data Size"
            },
            "legend": legendOptions,
            "tooltip": {
                "callbacks": {
                    "label": function (context) {
                        const value = context.parsed || 0;
                        const percentage = ((value / total_size) * 100).toFixed(1);
                        return `${formatSize(value)}/${percentage}%`;
                    }
                }
            }
        }
    }
});
charts.push(chart1);

wrapper = document.createElement('div');
wrapper.className = "pie";
canvas = document.createElement('canvas');
container.appendChild(wrapper);
wrapper.appendChild(canvas);
const ctx2 = canvas.getContext('2d');

const chart2 = new Chart(ctx2, {
    "type": "pie",
    "data": {
        "labels": Object.keys(data),
        "datasets": [{
            "label": "Index Size",
            "data": Object.values(data).map(item => item.index_size)
        }]
    },
    "options": {
        "plugins": {
            "title": {
                "display": true,
                "text": "Index Size"
            },
            "legend": legendOptions,
            "tooltip": {
                "callbacks": {
                    "label": function (context) {
                        const value = context.parsed || 0;
                        const percentage = ((value / total_index_size) * 100).toFixed(1);
                        return `${formatSize(value)}/${percentage}%`;
                    }
                }
            }
        }
    }
});
charts.push(chart2);

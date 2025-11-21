let wrapper = document.createElement('div');
let canvas = document.createElement('canvas');
wrapper.className = "pie";
canvas.className = 'pie';
container.appendChild(wrapper);
wrapper.appendChild(canvas);
const ctx = canvas.getContext('2d');
const chart = new Chart(ctx, {
    "type": "pie",
    "data": {
        "labels": Object.keys(data),
        "datasets": [{ "label": "Count", "data": Object.values(data) }],
    },
    "options": {
        "plugins": {
            "title": { "display": true, "text": "Version Distribution" },
            "tooltip": {
                "callbacks": {
                    "label": function (context) {
                        const value = context.parsed || 0;
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const percentage = ((value / total) * 100).toFixed(1);
                        return `${value} / ${percentage}%`;
                    }
                }
            }
        }
    },
});
charts.push(chart);
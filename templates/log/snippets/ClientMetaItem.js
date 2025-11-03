var driverCount = {};
data.forEach(doc => {
    const name = doc.doc.driver.name;
    if (driverCount[name] === undefined) {
        driverCount[name] = 0;
    }
    driverCount[name] += doc.ips.reduce((sum, ip) => sum + ip.count, 0);
});

var labels = Object.keys(driverCount);
var values = Object.values(driverCount);
var colors = labels.map((_, i) => `hsl(${i * 360 / labels.length}, 70%, 60%)`);

const ctx = document.getElementById('canvas_{name}').getContext('2d');
var chart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: labels,
        datasets: [{
            data: values,
            backgroundColor: colors
        }]
    },
    options: {
        plugins: {
            title: {
                display: true,
                text: 'Client By Driver'
            },
            legend: {
                position: 'right',
                labels: {
                    usePointStyle: true,
                    pointStyle: 'rect'
                }
            }
        }
    }
});
charts.push(chart);

var ipCount = {};
data.forEach(doc => {
    var ips = doc.ips.forEach(ip => {
        if (ipCount[ip.ip] === undefined) {
            ipCount[ip.ip] = 0;
        }
        ipCount[ip.ip] += ip.count;
    });
});
var labels = Object.keys(ipCount);
var values = Object.values(ipCount);
var colors = labels.map((_, i) => `hsl(${i * 360 / labels.length}, 70%, 60%)`);
const ctx_ip = document.getElementById('canvas_{name}_ip').getContext('2d');
var chart = new Chart(ctx_ip, {
    type: 'pie',
    data: {
        labels: labels,
        datasets: [{
            data: values,
            backgroundColor: colors
        }]
    },
    options: {
        plugins: {
            title: {
                display: true,
                text: 'Client By IP'
            },
            legend: {
                position: 'right',
                labels: {
                    usePointStyle: true,
                    pointStyle: 'rect'
                }
            }
        }
    }
});
charts.push(chart);
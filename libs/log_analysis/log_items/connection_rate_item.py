import json
import os
from libs.log_analysis.log_items.base_item import BaseItem
from datetime import datetime, timezone
from libs.log_analysis.shared import to_json
from bson import json_util
import math

class ConnectionRateItem(BaseItem):
    def __init__(self, output_folder: str, config):
        super(ConnectionRateItem, self).__init__(output_folder, config)
        self._cache = {}
        self.name = "Connection Rate"
        self.description = "Analyse the rate of connections created and ended over a specified time window."

    def analyze(self, log_line):
        msg = log_line.get("msg", "")
        if msg not in ["Connection accepted", "Connection ended"]:
            return
        counter = "created" if msg == "Connection accepted" else "ended"
        time = log_line.get("t")
        ts = math.floor(time.timestamp())
        time_min = datetime.fromtimestamp(ts - (ts % 60))

        if self._cache.get("time", None) != time_min:
            if self._cache != {}:
                self._write_output()
            self._cache = {
                "time": time_min,
                "created": 0,
                "ended": 0,
                "total": 0,
                "byIp": {}
            }
        attr = log_line.get("attr", {})
        conn_count = attr.get("connectionCount", 1)
        ip = attr["remote"].split(":")[0] if "remote" in attr else "unknown"
        self._cache[counter] += 1
        self._cache["total"] = conn_count
        if ip not in self._cache["byIp"]:
            self._cache["byIp"][ip] = {
                "created": 0,
                "ended": 0
            }
        self._cache["byIp"][ip][counter] += 1

    def review_results_markdown(self, f):
        super(ConnectionRateItem, self).review_results_markdown(f)
        f.write(f"<canvas id=\"canvas_{self.__class__.__name__}\" width=\"400\" height=\"200\"></canvas>\n")
        f.write(f"<canvas id=\"canvas_{self.__class__.__name__}_byip\" width=\"400\" height=\"200\"></canvas>\n")
        f.write(JS.replace("{self.__class__.__name__}", self.__class__.__name__))

JS = """
<script type="text/javascript">
var labels = [];
var created = [];
var destroyed = [];
var total = [];
data["{self.__class__.__name__}"].forEach(d => {
    labels.push(d.time);
    created.push(d.created);
    destroyed.push(-d.ended);
    total.push(d.total);
});

const ctx_{self.__class__.__name__} = document.getElementById('canvas_{self.__class__.__name__}').getContext('2d');
var chart = new Chart(ctx_{self.__class__.__name__}, {
  type: 'bar',
  data: {
    labels: labels,
    datasets: [
      {
        label: 'Connections Created',
        data: created,
        backgroundColor: 'rgba(54, 162, 235, 0.7)'
      },
      {
        label: 'Connections Destroyed',
        data: destroyed,
        backgroundColor: 'rgba(255, 99, 132, 0.7)'
      },
      {
        label: 'Total Connections',
        data: total,
        type: 'line',
        borderColor: 'rgba(255, 206, 86, 1)',
        backgroundColor: 'rgba(255, 206, 86, 0.2)',
        fill: false,
        yAxisID: 'y1',
        tension: 0.3,
        pointRadius: 2
      }
    ]
  },
  options: {
    responsive: true,
    plugins: {
      title: {
        display: true,
        text: 'Connection Create/Destroy Rate Over Time'
      },
      legend: { position: 'top' }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Connections per minute' }
      },
      y1: {
        beginAtZero: true,
        position: 'right',
        title: { display: true, text: 'Total Connections' },
        grid: { drawOnChartArea: false }
      }
    }
  }
});
charts.push(chart);

var rawData = data["{self.__class__.__name__}"];
var labels = rawData.map(d => d.time);
var ipSet = new Set();
rawData.forEach(d => Object.keys(d.byIp).forEach(ip => ipSet.add(ip)));
const ips = Array.from(ipSet);

const datasets = [];
ips.forEach(ip => {
  // created
  datasets.push({
    label: ip + ' created',
    data: rawData.map(d => d.byIp[ip]?.created || 0),
    stack: ip
  });
  // ended
  datasets.push({
    label: ip + ' ended',
    data: rawData.map(d => -(d.byIp[ip]?.ended || 0)),
    stack: ip
  });
});

const ctx_{self.__class__.__name__}_byip = document.getElementById('canvas_{self.__class__.__name__}_byip').getContext('2d');
var chart = new Chart(ctx_{self.__class__.__name__}_byip, {
  type: 'bar',
  data: {
    labels: labels,
    datasets: datasets
  },
  options: {
    plugins: {
      title: {
        display: true,
        text: 'Connections Created/Ended by IP per Minute'
      },
      legend: { position: 'top' }
    },
    responsive: true,
    scales: {
      x: { stacked: true },
      y: {
        stacked: true,
        beginAtZero: true,
        title: { display: true, text: 'Connections' }
      }
    }
  }
});
charts.push(chart);
</script>
"""
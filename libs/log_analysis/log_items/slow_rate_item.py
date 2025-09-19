import json
import os
from libs.log_analysis.log_items.base_item import BaseItem
from datetime import datetime, timezone
from libs.log_analysis.shared import to_json
from bson import json_util
import math

class SlowRateItem(BaseItem):
    def __init__(self, output_folder: str, config):
        super(SlowRateItem, self).__init__(output_folder, config)
        self._cache = {}
        self.name = "Slow Rate"
        self.description = "Analyse the rate of slow queries."

    def analyze(self, log_line):
        msg = log_line.get("msg", "")
        if msg != "Slow query":
            return
        time = log_line.get("t")
        ts = math.floor(time.timestamp())
        time_min = datetime.fromtimestamp(ts - (ts % 60))

        if self._cache.get("time", None) != time_min:
            if self._cache != {}:
                self._write_output()
            self._cache = {
                "time": time_min,
                "total_slow_ms": 0,
                "count": 0,
                "byNs": {}
            }
        attr = log_line.get("attr", {})
        slow_ms = attr.get("durationMillis", 0)
        ns = attr.get("ns", "unknown")
        self._cache["count"] += 1
        self._cache["total_slow_ms"] += slow_ms
        if ns not in self._cache["byNs"]:
            self._cache["byNs"][ns] = {
                "count": 0,
                "total_slow_ms": 0
            }
        self._cache["byNs"][ns]["count"] += 1
        self._cache["byNs"][ns]["total_slow_ms"] += slow_ms

    def review_results_markdown(self, f):
        super(SlowRateItem, self).review_results_markdown(f)
        f.write(f"<canvas id=\"canvas_{self.__class__.__name__}\" width=\"400\" height=\"200\"></canvas>\n")
        f.write(JS.replace("{self.__class__.__name__}", self.__class__.__name__))

JS = """
<script type="text/javascript">
var labels = [];
var count = [];
var total_slow_ms = [];
data["{self.__class__.__name__}"].forEach(d => {
    labels.push(d.time);
    count.push(d.count);
    total_slow_ms.push(d.total_slow_ms);
});

const ctx_{self.__class__.__name__} = document.getElementById('canvas_{self.__class__.__name__}').getContext('2d');
chart = new Chart(ctx_{self.__class__.__name__}, {
  type: 'bar',
  data: {
    labels: labels,
    datasets: [
      {
        label: 'Slow Count',
        data: count,
        backgroundColor: 'rgba(54, 162, 235, 0.7)',
        yAxisID: 'y'
      },
      {
        label: 'Total Slow (ms)',
        data: total_slow_ms,
        type: 'line',
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
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
      legend: { position: 'top' }
    },
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Count' }
      },
      y1: {
        beginAtZero: true,
        position: 'right',
        title: { display: true, text: 'Total Slow (ms)' },
        grid: { drawOnChartArea: false }
      }
    }
  }
});
charts.push(chart);
</script>
"""
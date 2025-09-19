from libs.log_analysis.log_items.base_item import BaseItem
from libs.log_analysis.shared import escape_markdown, json_hash, to_ejson
from bson import json_util
from libs.log_analysis.shared import to_json

class ClientMetaItem(BaseItem):
    def __init__(self, output_folder: str, config):
        super(ClientMetaItem, self).__init__(output_folder, config)
        self._cache = {}
        self.name = "Client Metadata"
        self.description = "Visualize client metadata."
        self._cache = {}

    def analyze(self, log_line):
        msg = log_line.get("msg", "")
        if msg != "client metadata":
            return
        attr = log_line.get("attr", {})
        ip = attr["remote"].split(":")[0]
        doc = attr["doc"]
        doc_hash = json_hash(doc)
        if doc_hash not in self._cache:
            self._cache[doc_hash] = {
                "doc": doc
            }
        if "ips" not in self._cache[doc_hash]:
            self._cache[doc_hash]["ips"] = {}
        self._cache[doc_hash]["ips"][ip] = self._cache[doc_hash]["ips"].get(ip, 0) + 1

    def finalize(self):
        with open(self._output_file, "a") as f:
            for v in self._cache.values():
                doc = v["doc"]
                ips = [{"ip": ip, "count": count} for ip, count in v.get("ips", {}).items()]
                f.write(to_ejson({
                    "doc": doc,
                    "ips": ips
                }))
                f.write("\n")

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f"|Application|Driver|OS|Platform|Client IPs|\n")
        f.write(f"|---|---|---|---|---|\n")
        with open(self._output_file, "r") as data:
            for line in data:
                line_json = json_util.loads(line)
                doc = line_json.get("doc", {})
                app = escape_markdown(doc.get("application", {}).get("name", "Unknown"))
                driver = doc.get("driver", {})
                driver_name = driver.get("name", "Unknown")
                driver_version = driver.get("version", "Unknown")
                driver_str = escape_markdown(f"{driver_name} {driver_version}")
                os = doc.get("os", {})
                os_type = os.get("type", "Unknown")
                os_name = os.get("name", "Unknown")
                os_arch = os.get("architecture", "Unknown")
                os_version = os.get("version", "Unknown")
                os_str = escape_markdown(f"{os_name if os_name != 'Unknown' else os_type} {os_arch} {os_version if os_version != 'Unknown' else ''}")
                platform = escape_markdown(doc.get("platform", "Unknown"))
                ips = [f"{ip['ip']} ({ip['count']} times)" for ip in line_json["ips"]]
                f.write(f"|{app}|{driver_str}|{os_str}|{platform}|{'<br/>'.join(ips)}|\n")
        f.write(f"<div class=\"pie\"><canvas id='canvas_{self.__class__.__name__}'></canvas></div>\n")
        f.write(f"<div class=\"pie\"><canvas id='canvas_{self.__class__.__name__}_ip'></canvas></div>\n")
        f.write(JS.replace("{self.__class__.__name__}", self.__class__.__name__))

JS = """
<script type="text/javascript">
var rawData = data["{self.__class__.__name__}"];

var driverCount = {};
rawData.forEach(doc => {
  const name = doc.doc.driver.name;
  if (driverCount[name] === undefined) {
    driverCount[name] = 0;
  }
  driverCount[name] += doc.ips.reduce((sum, ip) => sum + ip.count, 0);
});

var labels = Object.keys(driverCount);
var values = Object.values(driverCount);
var colors = labels.map((_, i) => `hsl(${i * 360 / labels.length}, 70%, 60%)`);

const ctx_{self.__class__.__name__} = document.getElementById('canvas_{self.__class__.__name__}').getContext('2d');
var chart = new Chart(ctx_{self.__class__.__name__}, {
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
      legend: { position: 'right' }
    }
  }
});
charts.push(chart);

var ipCount = {};
rawData.forEach(doc => {
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
const ctx_{self.__class__.__name__}_ip = document.getElementById('canvas_{self.__class__.__name__}_ip').getContext('2d');
var chart = new Chart(ctx_{self.__class__.__name__}_ip, {
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
      legend: { position: 'right' }
    }
  }
});
charts.push(chart);
</script>
"""
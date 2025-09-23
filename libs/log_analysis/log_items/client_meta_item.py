from libs.log_analysis.log_items.base_item import BaseItem
from libs.log_analysis.shared import escape_markdown, json_hash
from bson import json_util
from libs.utils import *

class ClientMetaItem(BaseItem):
    def __init__(self, output_folder: str, config):
        super(ClientMetaItem, self).__init__(output_folder, config)
        self._cache = {}
        self.name = "Client Metadata"
        self.description = "Visualize client metadata."
        self._cache = {}
        self._show_scaler = False

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
        cache = []
        for v in self._cache.values():
            doc = v["doc"]
            ips = [{"ip": ip, "count": count} for ip, count in v.get("ips", {}).items()]
            cache.append({
                "doc": doc,
                "ips": ips
            })
        self._cache = cache
        super().finalize()

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f"|Application|Driver|OS|Platform|Client IPs|\n")
        f.write(f"|---|---|---|---|---|\n")
        with open(self._output_file, "r") as data:
            for line in data:
                line_json = json_util.loads(line)
                doc = line_json.get("doc", {})
                full_app = doc.get("application", {}).get("name", "Unknown")
                trunc_app = truncate_content(full_app)
                app_html = tooltip_html(escape_markdown(full_app), escape_markdown(trunc_app)) if full_app != trunc_app else escape_markdown(full_app)
                driver = doc.get("driver", {})
                driver_name = driver.get("name", "Unknown")
                driver_version = driver.get("version", "Unknown")
                full_driver = escape_markdown(f"{driver_name} {driver_version}")
                os = doc.get("os", {})
                os_type = os.get("type", "Unknown")
                os_name = os.get("name", "Unknown")
                os_arch = os.get("architecture", "Unknown")
                os_version = os.get("version", "Unknown")
                os_str = escape_markdown(f"{os_name if os_name != 'Unknown' else os_type} {os_arch} {os_version if os_version != 'Unknown' else ''}")
                platform = escape_markdown(doc.get("platform", "Unknown"))
                ips = [f"{ip['ip']} ({ip['count']} times)" for ip in line_json["ips"]]
                f.write(f"|{app_html}|{full_driver}|{os_str}|{platform}|{'<br/>'.join(ips)}|\n")
        f.write(f"<div class=\"pie\"><canvas id='canvas_{self.__class__.__name__}'></canvas></div>\n")
        f.write(f"<div class=\"pie\"><canvas id='canvas_{self.__class__.__name__}_ip'></canvas></div>\n")
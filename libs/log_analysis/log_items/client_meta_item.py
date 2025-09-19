from libs.log_analysis.log_items.base_item import BaseItem
from libs.log_analysis.shared import escape_markdown, json_hash
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
        self._cache[doc_hash] = {
            "doc": doc
        }
        if "ips" not in self._cache[doc_hash]:
            self._cache[doc_hash]["ips"] = []
        self._cache[doc_hash]["ips"].append(ip)

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f"|Application|Driver|OS|Client IPs|\n")
        f.write(f"|---|---|---|---|\n")
        with open(self._output_file, "r") as data:
            # load all json lines
            for line in data:
                line_json = json_util.loads(line)
                for k,v in line_json.items():
                    doc = v.get("doc", {})
                    app = escape_markdown(doc.get("application", {}).get("name", "(Unknown)"))
                    driver = doc.get("driver", {})
                    driver_name = escape_markdown(driver.get("name", "(Unknown)"))
                    driver_version = escape_markdown(driver.get("version", "(Unknown)"))
                    os = doc.get("os", {})
                    os_type = escape_markdown(os.get("type", "(Unknown)"))
                    os_name = escape_markdown(os.get("name", "(Unknown)"))
                    os_arch = escape_markdown(os.get("architecture", "(Unknown)"))
                    os_version = escape_markdown(os.get("version", "(Unknown)"))
                    platform = escape_markdown(doc.get("platform", "(Unknown)"))
                    ips = v.get("ips", [])
                    f.write(f"|{app}|{driver_name} {driver_version}|{os_type} ({os_name}) {os_arch} {os_version}|{'<br/>'.join(ips)}|\n")
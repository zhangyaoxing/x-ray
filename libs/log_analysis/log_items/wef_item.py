from libs.log_analysis.log_items.base_item import BaseItem
from libs.log_analysis.shared import escape_markdown, json_hash
from bson import json_util
from libs.utils import *

class WEFItem(BaseItem):
    def __init__(self, output_folder, config):
        super().__init__(output_folder, config)
        self._cache = {}
        self.name = "Warning/Error/Fatal Logs"
        self.description = "Visualize warning, error, and fatal log messages."
        self._show_scaler = False

    def analyze(self, log_line):
        severity = log_line.get("s", "").lower()
        if severity not in ["w", "e", "f"]:
            return
        timestamp = log_line.get("t", "")
        msg = log_line.get("msg", "")
        id = log_line.get("id", "")
        if id not in self._cache:
            self._cache[id] = {
                "id": id,
                "severity": severity,
                "timestamp": [timestamp],
                "msg": msg,
                "sample": log_line
            }
        else:
            self._cache[id]["timestamp"].append(timestamp)

    def finalize(self):
        self._cache = list(self._cache.values())
        super().finalize()

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f"|ID|Severity|Message|Count|\n")
        f.write(f"|---|---|---|---|\n")
        rows = []
        with open(self._output_file, "r") as data:
            for line in data:
                line_json = json_util.loads(line)
                id = line_json.get("id", "Unknown")
                severity = line_json.get("severity", "Unknown").upper()
                msg = line_json.get("msg", "")
                count = len(line_json.get("timestamp", []))
                rows.append(f"|{id}|{severity}|{escape_markdown(msg)}|{count}|\n")
        rows = sorted(rows, key=lambda x: x.lower())
        for row in rows:
            f.write(row)

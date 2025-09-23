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
                self._row_count += 1
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

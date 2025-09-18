import os
from libs.log_analysis.log_items.base_item import BaseItem
from datetime import datetime, timezone
from libs.log_analysis.shared import to_json
import math

class ConnectionRateItem(BaseItem):
    def __init__(self, output_folder: str, config):
        super(ConnectionRateItem, self).__init__(output_folder, config)
        self._cache = {}

    def analyze(self, log_line):
        msg = log_line.get("msg", "")
        if msg not in ["Connection accepted", "Connection ended"]:
            return
        counter = "created" if msg == "Connection accepted" else "ended"
        time = log_line.get("t")
        ts = math.floor(time.timestamp())
        time_min = datetime.fromtimestamp(ts - (ts % 60))

        if self._cache.get("time", None) != time_min:
            if self._cache == {}:
                # First time, remove the output file if it exists.
                # This is only possible when running in development mode.
                os.remove(self._output_file) if os.path.isfile(self._output_file) else None
            else:
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

    def _write_output(self):
        # Open file steam and write the cache to file
        with open(self._output_file, "a") as f:
            f.write(to_json(self._cache))
            f.write("\n")

    @property
    def name(self):
        return "Connection Rate Item"

    @property
    def description(self):
        return "Analyzes the rate of connections per IP address over a specified time window."
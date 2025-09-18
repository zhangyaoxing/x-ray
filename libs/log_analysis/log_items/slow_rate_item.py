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


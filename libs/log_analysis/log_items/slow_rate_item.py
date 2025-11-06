"""Analyze slow query rates from log lines."""

from datetime import datetime
import math
from libs.log_analysis.log_items.base_item import BaseItem


class SlowRateItem(BaseItem):
    def __init__(self, output_folder: str, config):
        super().__init__(output_folder, config)
        self._cache = None
        self.name = "Slow Rate"
        self.description = "Analyse the rate of slow queries."
        self._show_reset = True

    def analyze(self, log_line):
        log_id = log_line.get("id", "")
        if log_id != 51803:  # Slow query
            return
        time = log_line.get("t")
        ts = math.floor(time.timestamp())
        time_min = datetime.fromtimestamp(ts - (ts % 60))

        if self._cache is None or self._cache["time"] != time_min:
            if self._cache is not None:
                # New minute, write previous minute's data
                self._write_output()
            # First time or new minute bucket
            self._cache = {"time": time_min, "total_slow_ms": 0, "count": 0, "byNs": {}}

        attr = log_line.get("attr", {})
        slow_ms = attr.get("durationMillis", 0)
        ns = attr.get("ns", "unknown")
        self._cache["count"] += 1
        self._cache["total_slow_ms"] += slow_ms
        if ns not in self._cache["byNs"]:
            self._cache["byNs"][ns] = {"count": 0, "total_slow_ms": 0}
        self._cache["byNs"][ns]["count"] += 1
        self._cache["byNs"][ns]["total_slow_ms"] += slow_ms

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f'<canvas id="canvas_{self.__class__.__name__}" width="400" height="200"></canvas>\n')
        f.write(f'<div class="pie"><canvas id="canvas_{self.__class__.__name__}_byns" height="200"></canvas></div>\n')
        f.write(
            f'<div class="pie"><canvas id="canvas_{self.__class__.__name__}_byns_ms" height="200"></canvas></div>\n'
        )

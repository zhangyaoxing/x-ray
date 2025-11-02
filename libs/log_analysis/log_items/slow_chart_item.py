from libs.log_analysis.log_items.base_item import BaseItem
class SlowChartItem(BaseItem):
    def __init__(self, output_folder, config):
        super().__init__(output_folder, config)
        self.name = "Slow Operations Chart"
        self.description = "Generate a scatter plot showing slow operations over time, with each point representing a slow query colored by namespace."
        self._show_scaler = False
        self._show_reset = True
        self._cache = None
    
    def analyze(self, log_line):
        log_id = log_line.get("id", "")
        if log_id != 51803:  # Slow query
            return
        self._cache = log_line
        self._write_output()
        self._cache = None

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write(f"<div id=\"links_{self.__class__.__name__}\" markdown=\"1\">\n")
        f.write(f"[Duration Chart](#canvas_{self.__class__.__name__}_duration)")
        f.write(f" \| [Scanned Chart](#canvas_{self.__class__.__name__}_scanned)")
        f.write(f" \| [Scanned Objects Chart](#canvas_{self.__class__.__name__}_scannedObj)")
        f.write(f"</div>\n")
        f.write(f"<canvas id=\"canvas_{self.__class__.__name__}_duration\" height=\"200\"></canvas>\n")
        f.write(f"<canvas id=\"canvas_{self.__class__.__name__}_scanned\" height=\"200\" style=\"display: none;\"></canvas>\n")
        f.write(f"<canvas id=\"canvas_{self.__class__.__name__}_scannedObj\" height=\"200\" style=\"display: none;\"></canvas>\n")
        f.write(f"<div id=\"positioner_{self.__class__.__name__}\"></div>\n")
        f.write(f"```json\n")
        f.write(f"// Click data points to review original log line...\n")
        f.write(f"```\n")
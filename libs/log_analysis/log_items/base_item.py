import logging
import os

from libs.log_analysis.shared import MAX_DATA_POINTS, to_json
from bson import json_util
from libs.utils import get_script_path
from libs.version import Version
from libs.utils import to_ejson

def get_version(log_line):
    """
    Extract and parse the version information from a log line.
    """
    log_id = log_line.get("id", "")
    if log_id != 23403:
        return None
    attr = log_line.get("attr", {})
    build_info = attr.get("buildInfo", {})
    version = build_info.get("version", "Unknown")
    return Version.parse(version)

class BaseItem(object):
    def __init__(self, output_folder: str, config):
        self.config = config
        self._output_file = os.path.join(output_folder, f"{self.__class__.__name__}.json")
        self._logger = logging.getLogger(__name__)
        self._row_count = 0
        self._show_scaler = True
        self._show_reset = False
        self._server_version = None
        os.remove(self._output_file) if os.path.isfile(self._output_file) else None

    def analyze(self, log_line):
        log_id = log_line.get("id", "")
        if log_id == 23403: # Build Info
            self._server_version = get_version(log_line)

    def review_results(self):
        raise NotImplementedError("Subclasses must implement the review_results method.")
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    def finalize_analysis(self):
        self._write_output()

    def review_results_markdown(self, f):
        # Calculate the scale for the chart. Avoid too many data points.
        scale = round(self._row_count / MAX_DATA_POINTS if self._row_count > MAX_DATA_POINTS else 1)
        # Write JS snippet to the file
        file_name = f"{self.__class__.__name__}.js"
        file_path = os.path.join("templates", "log", "snippets", file_name)
        file_path = get_script_path(file_path)
        self._logger.debug(f"Using JS snippet file: {file_path}")
        
        f.write(f"## {self.name}\n\n")
        f.write(f"{self.description}\n\n")
        if self._show_scaler:
            f.write("<div style=\"display: none;\">\n")
            f.write(f"*Total data points: `{self._row_count}`, displaying every <input type=\"range\" id=\"slider_{self.__class__.__name__}\" min=\"1\" max=\"{scale * 2}\" value=\"{scale}\">")
            f.write(f"<code id=\"sliderValue_{self.__class__.__name__}\">{scale}</code> point(s).*\n\n")
            f.write("</div>\n\n")
        if self._show_reset:
            f.write(f"<input type=\"button\" id=\"reset_{self.__class__.__name__}\" value=\"Reset\">\n\n")
        f.write("<script type=\"text/javascript\">\n")
        f.write("document.addEventListener('DOMContentLoaded', function() {\n")
        if self._show_scaler:
            f.write(f"let slider = document.getElementById('slider_{self.__class__.__name__}');\n")
            f.write(f"let sliderValue = document.getElementById('sliderValue_{self.__class__.__name__}');\n")
            f.write("slider.oninput = function() {\n")
            f.write(f"  let value = parseInt(slider.value);\n")
            f.write(f"  sliderValue.textContent = value;\n")
            f.write("}\n")
            f.write("slider.onchange = function() {\n")
            f.write("  onSlide(slider, sliderValue, scaleCharts);\n")
            f.write("}\n")
            f.write("let scale = parseInt(sliderValue.innerText);\n")
        if self._show_reset:
            f.write(f"let resetButton = document.getElementById('reset_{self.__class__.__name__}');\n")
        f.write(f"let data = [\n")
        with open(self._output_file, "r") as data:
            for line in data:
                # The data is in EJSON format, convert it to JSON
                line_json = json_util.loads(line)
                f.write(to_json(line_json))
                f.write(", \n")
        f.write("];\n")
        if os.path.isfile(file_path):
            with open(file_path, "r") as js:
                for line in js:
                    f.write(line.replace("{name}", self.__class__.__name__))
        f.write("});\n")
        f.write("</script>\n")

    def _write_output(self):
        # Open file steam and write the cache to file
        # Even if the cache is None, we still write to indicate no data
        with open(self._output_file, "a") as f:
            if self._cache is None:
                self._logger.debug(f"Cache is empty, nothing to write for {self.__class__.__name__}")
                return
            if isinstance(self._cache, list):
                for item in self._cache:
                    f.write(to_ejson(item, indent=None))
                    f.write("\n")
                    self._row_count += 1
                self._logger.debug(f"Wrote {len(self._cache)} records to {self._output_file} for {self.__class__.__name__}")
            else:
                f.write(to_ejson(self._cache, indent=None))
                f.write("\n")
                self._row_count += 1
                self._logger.debug(f"Wrote 1 record to {self._output_file} for {self.__class__.__name__}")
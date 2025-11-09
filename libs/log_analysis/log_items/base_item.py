import logging
import os
from bson import json_util
from libs.log_analysis.shared import to_json
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


class BaseItem:
    _cache = None

    def __init__(self, output_folder: str, config, **kwargs):
        self.config = config
        self._output_file = os.path.join(output_folder, f"{self.__class__.__name__}.json")
        self._logger = logging.getLogger(__name__)
        self._row_count = 0
        self._show_reset = kwargs.get("show_reset", False)
        self._server_version = None
        if os.path.isfile(self._output_file):
            os.remove(self._output_file)

    def analyze(self, log_line):
        log_id = log_line.get("id", "")
        if log_id == 23403:  # Build Info
            self._server_version = get_version(log_line)

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
        # Write JS snippet to the file
        file_name = f"{self.__class__.__name__}.js"
        file_path = os.path.join("templates", "log", "snippets", file_name)
        file_path = get_script_path(file_path)
        self._logger.debug("Using JS snippet file: %s", file_path)

        f.write(f"## {self.name}\n\n")
        f.write(f"{self.description}\n\n")

        if self._show_reset:
            f.write(f'<input type="button" id="reset_{self.__class__.__name__}" value="Reset">\n\n')
        f.write('<script type="text/javascript">\n')
        f.write("document.addEventListener('DOMContentLoaded', function() {\n")
        if self._show_reset:
            f.write(f"let resetButton = document.getElementById('reset_{self.__class__.__name__}');\n")
        f.write("let data = [\n")
        with open(self._output_file, "r", encoding="utf-8") as data:
            for line in data:
                # The data is in EJSON format, convert it to JSON
                line_json = json_util.loads(line)
                f.write(to_json(line_json))
                f.write(", \n")
        f.write("];\n")
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as js:
                for line in js:
                    f.write(line.replace("{name}", self.__class__.__name__))
        f.write("});\n")
        f.write("</script>\n")

    def _write_output(self):
        # Open file steam and write the cache to file
        # Even if the cache is None, we still write to indicate no data
        with open(self._output_file, "a", encoding="utf-8") as f:
            if self._cache is None:
                self._logger.debug("Cache is empty, nothing to write for %s", self.__class__.__name__)
                return
            if isinstance(self._cache, list):
                for item in self._cache:
                    f.write(to_ejson(item, indent=None))
                    f.write("\n")
                    self._row_count += 1
                self._logger.debug(
                    "Wrote %d records to %s for %s",
                    len(self._cache),
                    self._output_file,
                    self.__class__.__name__,
                )
            else:
                f.write(to_ejson(self._cache, indent=None))
                f.write("\n")
                self._row_count += 1
                self._logger.debug(
                    "Wrote 1 record to %s for %s",
                    self._output_file,
                    self.__class__.__name__,
                )

import logging
import os

from libs.log_analysis.shared import to_ejson, to_json
from bson import json_util

class BaseItem(object):
    def __init__(self, output_folder: str, config):
        self.config = config
        self._output_file = os.path.join(output_folder, f"{self.__class__.__name__}.json")
        self._logger = logging.getLogger(__name__)

    def analyze(self, log_line):
        raise NotImplementedError("Subclasses must implement the analyze method.")

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

    
    def finalize(self):
        self._write_output()

    def review_results_markdown(self, f):
        f.write(f"## {self.name}\n\n")
        f.write(f"{self.description}\n\n")
        f.write("<script type=\"text/javascript\">\n")
        f.write(f"data['{self.__class__.__name__}'] = [\n")
        with open(self._output_file, "r") as data:
            for line in data:
                # The data is in EJSON format, convert it to JSON
                line_json = json_util.loads(line)
                f.write(to_json(line_json))
                f.write(", \n")
        f.write("];\n")
        f.write("</script>\n")

    def _write_output(self):
        # Open file steam and write the cache to file
        with open(self._output_file, "a") as f:
            f.write(to_ejson(self._cache))
            f.write("\n")
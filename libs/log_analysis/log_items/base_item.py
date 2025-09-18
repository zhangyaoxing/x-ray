
import logging
import os

class BaseItem(object):
    def __init__(self, output_folder: str, config):
        self.config = config
        self._output_file = os.path.join(output_folder, f"{self.__class__.__name__}.json")
        self._logger = logging.getLogger(__name__)

    def analyze(self, log_line):
        raise NotImplementedError("Subclasses must implement the analyze method.")

    @property
    def name(self):
        raise NotImplementedError("Subclasses must implement the name method.")

    @property
    def description(self):
        raise NotImplementedError("Subclasses must implement the description method.")
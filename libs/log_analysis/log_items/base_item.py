
import logging
import os

class BaseItem(object):
    def __init__(self, output_folder: str, config):
        self.config = config
        self._output_file = os.path.join(output_folder, f"{self.__class__.__name__}.json")
        self._logger = logging.getLogger(__name__)

    def analyze(self, log_line):
        raise NotImplementedError("Subclasses must implement the analyze method.")

    def finalize(self):
        raise NotImplementedError("Subclasses must implement the finalize method.")

    def review_results(self):
        raise NotImplementedError("Subclasses must implement the review_results method.")
    
    def review_results_markdown(self, f):
        raise NotImplementedError("Subclasses must implement the review_results_markdown method.")

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
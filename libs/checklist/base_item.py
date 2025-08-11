from abc import abstractmethod
from enum import Enum
import logging
from bson import json_util
from libs.utils import env

class SEVERITY(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4

def colorize_severity(severity: SEVERITY) -> str:
    if severity == SEVERITY.HIGH:
        return "red"
    elif severity == SEVERITY.MEDIUM:
        return "orange"
    elif severity == SEVERITY.LOW:
        return "gray"
    else:
        return "blue"

class BaseItem:
    def __init__(self, output_folder: str, config: dict = None):
        self._name = "BaseItem"
        self._description = "Base item for checklist framework. If you see this, it means the item is not properly defined."
        self._config = config or {}
        self._test_result = []
        self._logger = logging.getLogger(__name__)
        self._output_folder = output_folder

    @abstractmethod
    def test(self):
        pass

    @property
    def name(self):
        return self._name
    
    @property
    def description(self):
        return self._description

    @property
    def sample_result(self):
        with open(self.cache_file_name, "r") as f:
            return json_util.loads(f.read())
        
    @property
    def test_result(self):
        return {
            "name": self.name,
            "description": self.description,
            "items": self._test_result
        }
    
    @property
    def test_result_markdown(self):
        result = ""
        if len(self._test_result) == 0:
            result += "<b style='color: green;'>All pass.</b>\n\n"
            return result
        
        result += "| \\# | Severity | Category | Message |\n"
        result += "|----------|----------|---------|---------|\n"
        for idx, item in enumerate(self._test_result):
            result += f"| **{idx + 1}** | <b style='color: {colorize_severity(item['severity'])}'> {item['severity'].name} </b> | {item['title']} | {item['message']} |\n"
        result += "\n"
        return result
        
    @sample_result.setter
    def sample_result(self, data):
        with open(self.cache_file_name, "w") as f:
            if env == "development":
                # Pretty print in development mode for easier debugging
                f.write(json_util.dumps(data, indent=4))
            else:
                f.write(json_util.dumps(data))

    @property
    def cache_file_name(self):
        return f"{self._output_folder}/{self.__class__.__name__}.json"
    
    def append_item_result(self, severity: SEVERITY, title: str, message: str):
        self._test_result.append({
            "severity": severity,
            "title": title,
            "message": message
        })
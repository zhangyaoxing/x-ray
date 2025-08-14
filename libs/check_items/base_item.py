from abc import abstractmethod
import logging
from bson import json_util
from libs.shared import SEVERITY
from libs.utils import env

def colorize_severity(severity: SEVERITY) -> str:
    if severity == SEVERITY.HIGH:
        return "red"
    elif severity == SEVERITY.MEDIUM:
        return "orange"
    elif severity == SEVERITY.LOW:
        return "green"
    elif severity == SEVERITY.INFO:
        return "gray"

class BaseItem:
    def __init__(self, output_folder: str, config: dict = None):
        self._name = "BaseItem"
        self._description = "Base item for checklist framework. If you see this, it means the item is not properly defined."
        self._config = config or {}
        self._test_result = []
        self._logger = logging.getLogger(self.__class__.__name__)
        self._output_folder = output_folder

    @abstractmethod
    def test(self, *args, **kwargs):
        pass

    @property
    def name(self):
        return self._name
    
    @property
    def description(self):
        return self._description

    @property
    def captured_sample(self):
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
        
        result += "| \\# | Host | Severity | Category | Message |\n"
        result += "|:----------:|:----------:|:----------:|---------|---------|\n"
        for idx, item in enumerate(self._test_result):
            result += f"| **{idx + 1}** | `{item['host']}` | <b style='color: {colorize_severity(item['severity'])}'> {item['severity'].name} </b> | {item['title']} | {item['message']} |\n"
        result += "\n"
        return result

    @property
    def review_result(self):
        return {
            "name": self.name,
            "description": self.description,
            "data": []
        }

    @property
    def review_result_markdown(self):
        result_data = self.review_result["data"]
        result = ""
        for i, block in enumerate(result_data):
            type = block.get("type")
            caption = block.get("caption")
            if type == "table":
                result += f"### ({i + 1}) {block.get('caption')}\n"
                result += "| " + " | ".join(col.get("name") for col in block.get("columns", [])) + " |\n"
                result += "|:----------:|" + "|:----------:|" * (len(block.get("columns", [])) - 1) + "\n"
                for row in block.get("rows", []):
                    result += "| " + " | ".join(str(cell) for cell in row) + " |\n"
            # TODO: support other types.
        return result

    @captured_sample.setter
    def captured_sample(self, data):
        with open(self.cache_file_name, "w") as f:
            if env == "development":
                # Pretty print in development mode for easier debugging
                f.write(json_util.dumps(data, indent=4))
            else:
                f.write(json_util.dumps(data))

    @property
    def cache_file_name(self):
        return f"{self._output_folder}/{self.__class__.__name__}_raw.json"
    
    def append_item_result(self, host: str, severity: SEVERITY, title: str, message: str):
        self._test_result.append({
            "host": host,
            "severity": severity,
            "title": title,
            "message": message
        })
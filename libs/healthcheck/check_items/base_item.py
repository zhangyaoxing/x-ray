from abc import abstractmethod
import logging
import gzip
import os
from bson import json_util
from libs.healthcheck.shared import SEVERITY, to_json
from libs.utils import env, get_script_path, to_ejson


def colorize_severity(severity: SEVERITY) -> str:
    mapping = {
        SEVERITY.HIGH.name: "red",
        SEVERITY.MEDIUM.name: "orange",
        SEVERITY.LOW.name: "green",
        SEVERITY.INFO.name: "gray",
    }
    return mapping.get(severity.name, "black")


TABLE_ALIGNMENT = {
    "left": ":----------",
    "right": "----------:",
    "center": ":----------:",
}


class BaseItem:
    _name: str
    _description: str
    _test_result: list
    _config: dict

    def __init__(self, output_folder: str, config: dict = None, **kwargs):
        self._config = config or {}
        self._test_result = []
        self._logger = logging.getLogger(self.__class__.__name__)
        self._output_folder = output_folder if output_folder.endswith("/") else f"{output_folder}/"

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
        try:
            if self.cache_file_name.endswith(".gz"):
                with gzip.open(self.cache_file_name, "rt") as f:
                    return json_util.loads(f.read())
            else:
                with open(self.cache_file_name, "r", encoding="utf-8") as f:
                    return json_util.loads(f.read())
        except FileNotFoundError:
            return None

    @property
    def test_result(self):
        return {
            "name": self.name,
            "description": self.description,
            "items": self._test_result,
        }

    @property
    def test_result_markdown(self):
        result = ""
        if len(self._test_result) == 0:
            result += "<b style='color: green;'>Pass.</b>\n\n"
            return result

        result += "| \\# | Host | Severity | Category | Message |\n"
        result += "|:----------:|:----------:|:----------:|---------|---------|\n"
        for idx, item in enumerate(self._test_result):
            result += f"| **{idx + 1}** | `{item['host']}` | <b style='color: {colorize_severity(item['severity'])}'> {item['severity'].name} </b> | {item['title']} | {item['message']} |\n"
        result += "\n"
        return result

    @property
    def review_result(self):
        return {"name": self.name, "description": self.description, "data": []}

    @property
    def review_result_markdown(self):
        result_data = self.review_result["data"]
        result = ""
        if len(result_data) == 0:
            result += "(No data)\n\n"
            return result
        i = 0
        # Output tables first because they are static in markdown.
        for j, block in enumerate(result_data):
            chart_type = block.get("type")
            caption = block.get("caption")
            notes = block.get("notes", "")
            if chart_type == "table":
                result += f"#### ({i + 1}) {caption}\n"
                result += f"{notes}\n"
                header = [col.get("name", "(NOT SET)") for col in block.get("columns", [])]
                align = [
                    TABLE_ALIGNMENT.get(col.get("align", "center"), TABLE_ALIGNMENT["center"])
                    for col in block.get("columns", [])
                ]
                result += f"|{'|'.join(header)}|\n"
                result += f"|{'|'.join(align)}|\n"
                for row in block.get("rows", []):
                    result += "|" + "|".join(str(cell) for cell in row) + "|\n"
                result += "\n"
                i += 1

        result += f'<div id="container_{self.__class__.__name__}"></div>'
        # Output charts next because they are dynamic via JavaScript and need to be in the same context.
        result += "<script type='text/javascript'>\n"
        result += "(function() {\n"
        for j, block in enumerate(result_data):
            chart_type = block.get("type")
            if chart_type != "table":
                result += f"let data_{j} = {to_json(block.get('data'))};\n"
        # Run the JS snippets
        file_name = f"{self.__class__.__name__}.js"
        file_path = os.path.join("templates", "healthcheck", "snippets", file_name)
        file_path = get_script_path(file_path)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as js_file:
                for line in js_file:
                    result += line.replace("{name}", self.__class__.__name__)
        result += "})()\n"
        result += "</script>\n"
        return result

    @captured_sample.setter
    def captured_sample(self, data):
        if self.cache_file_name.endswith(".gz"):
            with gzip.open(self.cache_file_name, "wt") as f:
                f.write(to_ejson(data))
        else:
            with open(self.cache_file_name, "w", encoding="utf-8") as f:
                f.write(to_ejson(data))

    @property
    def cache_file_name(self):
        if env == "development":
            return f"{self._output_folder}{self.__class__.__name__}_raw.json"
        return f"{self._output_folder}{self.__class__.__name__}_raw.json.gz"

    def append_test_result(self, host: str, severity: SEVERITY, title: str, message: str):
        self._test_result.append({"host": host, "severity": severity, "title": title, "message": message})

    def append_test_results(self, items: list):
        for item in items:
            self.append_test_result(item["host"], item["severity"], item["title"], item["description"])

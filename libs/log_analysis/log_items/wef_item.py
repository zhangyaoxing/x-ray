from random import randint
from libs.log_analysis.log_items.base_item import BaseItem
from libs.log_analysis.shared import escape_markdown, json_hash
from bson import json_util
from libs.utils import *
from libs.log_analysis.shared import AI_MODEL

class WEFItem(BaseItem):
    def __init__(self, output_folder, config):
        super().__init__(output_folder, config)
        self._cache = {}
        self.name = "Warning/Error/Fatal Logs"
        self.description = "Visualize warning, error, and fatal log messages."
        self._show_scaler = False

    def analyze(self, log_line):
        severity = log_line.get("s", "").lower()
        if severity not in ["w", "e", "f"]:
            return
        timestamp = log_line.get("t", "")
        msg = log_line.get("msg", "")
        id = log_line.get("id", "")
        if id not in self._cache:
            self._cache[id] = {
                "id": id,
                "severity": severity,
                "timestamp": [timestamp],
                "msg": msg,
                "sample": log_line
            }
        else:
            self._cache[id]["timestamp"].append(timestamp)

    def finalize_analysis(self):
        self._cache = list(self._cache.values())
        # Ask AI about the warning/error/fatal messages
        if ai_key != "":
            self._logger.info(bold(green("AI API key found.")) + f" Analyzing W/E/F logs with AI ({green(bold(AI_MODEL))}). This can take a few minutes...")
            from openai import OpenAI
            client = OpenAI()

            if env == "development":
                cache = [self._cache[randint(0, len(self._cache) - 1)]] if len(self._cache) > 0 else []
                self._logger.info(yellow(f"Running in development mode. Only process ONE random log entry with AI."))
                self._logger.info(yellow(f"Log ID: {cache[0]['id']}"))
            for item in cache:
                response = client.responses.create(
                    model=AI_MODEL,
                    input=f"Tell me about this MongoDB log. Keep the answer as short as possible: {str(item['sample'])}",
                )
                item["ai_analysis"] = response.output_text
                self._logger.debug(f"AI analyzed log: {item['id']}")
        
        super().finalize_analysis()

    def review_results_markdown(self, f):
        super().review_results_markdown(f)
        f.write("<div id=\"wef_positioner\"></div>\n\n")
        f.write(f"|Code|Severity|Message|Count|\n")
        f.write(f"|---|---|---|---|\n")
        rows = []
        i = 0
        with open(self._output_file, "r") as data:
            for line in data:
                line_json = json_util.loads(line)
                id = line_json.get("id", "Unknown")
                severity = line_json.get("severity", "Unknown").upper()
                msg = line_json.get("msg", "")
                count = len(line_json.get("timestamp", []))
                rows.append(f"|[{id}](#{i})|{severity}|{escape_markdown(msg)}|{count}|\n")
                i += 1
        rows = sorted(rows, key=lambda x: x.lower())
        for row in rows:
            f.write(row)
        f.write(f"```json\n")
        f.write(f"// Click error code to review sample log line...\n")
        f.write(f"```\n")
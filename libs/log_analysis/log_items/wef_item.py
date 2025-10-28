from random import randint
from libs.log_analysis.log_items.base_item import BaseItem
from libs.log_analysis.shared import escape_markdown, json_hash
from bson import json_util
from libs.utils import *

class WEFItem(BaseItem):
    def __init__(self, output_folder, config):
        super().__init__(output_folder, config)
        self._cache = {}
        self.name = "Warning/Error/Fatal Logs"
        self.description = "Visualize warning, error, and fatal log messages."
        self._show_scaler = False
        self._ai_support = self.config.get("ai_support", False)

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
        cache = self._cache
        
        # Lazy import AI modules (only if needed)
        if self._ai_support in ["local"]:
            try:
                from libs.ai import MODEL_NAME, GPT_MODEL, analyze_log_line_gpt, analyze_log_line_local, load_model
            except ImportError as e:
                self._logger.error(f"AI support enabled but AI libraries not available: {e}")
                self._logger.error("Please install AI dependencies or disable AI support in config.json")
                self._ai_support = False
        
        if self._ai_support == "local":
            tokenizer, model, gen_config = load_model(MODEL_NAME)
            self._logger.info(f"Local AI model ({green(bold(MODEL_NAME))}) loaded for W/E/F log analysis.")
        elif self._ai_support == "gpt":
            if env == "development":
                cache = [self._cache[randint(0, len(self._cache) - 1)]] if len(self._cache) > 0 else []
                self._logger.info(yellow(f"Running in development mode. Only process ONE random log entry with AI."))
                self._logger.info(yellow(f"Log ID: {cache[0]['id']}"))
            self._logger.info(f"Using GPT model ({green(bold(GPT_MODEL))}) for W/E/F log analysis. This can take a few minutes...")

        for item in cache:
            if self._ai_support == "local":
                item["ai_analysis"] = analyze_log_line_local(item["sample"], tokenizer, model, gen_config)
            elif self._ai_support == "gpt":
                item["ai_analysis"] = analyze_log_line_gpt(item["sample"])

            if self._ai_support:
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
from datetime import datetime, timezone
import random
import re
from libs.healthcheck.shared import to_json, to_markdown_id, irresponsive_nodes
from libs.utils import *
import logging
import importlib
import pkgutil
import markdown
from bson import json_util

logger = logging.getLogger(__name__)
def load_log_classes(package_name="libs.log_analysis.log_items"):
    class_map = {}
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package_name}.{module_name}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type):
                class_map[attr] = obj
    logger.debug(f"Loaded log analysis classes: {list(class_map.keys())}")
    return class_map
LOG_CLASSES = load_log_classes()

class Framework:
    def __init__(self, file_path: str, config: dict):
        self._file_path = file_path
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._items = []
        now = str(datetime.now(tz=timezone.utc))
        self._timestamp = re.sub(r"[:\- ]", "", now.split(".")[0])
        self._logger.debug(to_json(self._config))
        self._log_start = None
        self._log_end = None
        if env == "development":
            self._logger.info(yellow("Running in development mode."))

    def _get_output_folder(self, output_folder: str):
        if env == "development":
            batch_folder = output_folder
        else:
            batch_folder = f"{output_folder}{self._logset_name}-{self._timestamp}/"
            Path(batch_folder).mkdir(parents=True, exist_ok=True)
        return batch_folder

    def run_logs_analysis(self, logset_name: str, *args, **kwargs):
        self._logset_name = logset_name
        # Create output folder if it doesn't exist
        output_folder = kwargs.get("output_folder", "output/")
        batch_folder = self._get_output_folder(output_folder)
        # Dynamically load the log checkset based on the name
        logsets = self._config.get("logsets", {})
        if not logset_name in logsets:
            self._logger.warning(yellow(f"Log checkset '{logset_name}' not found in configuration. Using default logset."))
            logset_name = "default"
        ls = logsets[logset_name]
        self._logger.info(f"Running log checkset: {bold(green(logset_name))}")

        self._items = []
        for item_name in ls.get("items", []):
            item_cls = LOG_CLASSES.get(item_name)
            if not item_cls:
                self._logger.warning(yellow(f"Log item '{item_name}' not found. Skipping."))
                continue
            # The config for the item can be specified in the `item_config` section, under the item class name.
            item_config = ls.get("item_config", {}).get(item_name, {})
            item = item_cls(batch_folder, item_config)
            self._items.append(item)
            self._logger.info(f"Log analyze item loaded: {bold(cyan(item_name))}")
        log_file = self._file_path
        rate = self._config.get("sample_rate", 1.0)
        # Read the log file line by line and pass each line to the log items for analysis
        log_line = None
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            counter = 0
            for line in f:
                counter += 1
                if counter % 10000 == 0:
                    self._logger.info(f"{green(counter)} lines ingested...")
                # Sampling based on the rate. For dealing with large log files.
                if random.random() > rate:
                    continue
                try:
                    log_line = json_util.loads(line)
                    if self._log_start is None:
                        self._log_start = log_line.get("t", None)
                    for item in self._items:
                        try:
                            item.analyze(log_line)
                        except Exception as e:
                            self._logger.warning(yellow(f"Log analysis item '{item.name}' failed: {e}"))
                            continue
                except Exception as e:
                    self._logger.warning(yellow(f"Failed to parse log line as JSON: {line.strip()}"))
                    continue
        self._log_end = log_line.get("t", None) if log_line else None
        for item in self._items:
            try:
                item.finalize_analysis()
            except Exception as e:
                self._logger.warning(yellow(f"Log analysis item '{item.name}' finalize failed: {e}"))
                continue
        
    def output_results(self, output_folder: str = "output/", format: str = "html"):
        batch_folder = self._get_output_folder(output_folder)
        output_file = f"{batch_folder}report.md"
        template_file = get_script_path(f"templates/{self._config.get('template', 'log/full.html')}")
        self._logger.info(f"Saving results to: {green(output_file)}")

        with open(output_file, "w") as f:
            f.write(f"# Log Analysis Report\n")
            f.write(f"Generated at: `{str(datetime.now(tz=timezone.utc))} UTC`\n\n")
            f.write(f"Log path: `{self._file_path}`\n\n")
            f.write(f"Log analysis period: `{self._log_start.isoformat()}` to `{self._log_end.isoformat()}`\n\n")
            f.write("Histogram chart instructions:\n\n")
            f.write("- **zoom in/out:** _mouse wheel or pinch_\n")
            f.write("- **pan:** _shift+drag_\n")
            f.write("- **select time frame:** _drag_\n\n")
            for item in self._items:
                try:
                    item.review_results_markdown(f)
                except Exception as e:
                    self._logger.warning(yellow(f"Failed to generate markdown for log item '{item.name}': {e}"))
                    continue

        if format == "html":
            html_file = f"{batch_folder}report.html"
            self._logger.info(f"Converting markdown to HTML: {green(html_file)}")
            with open(html_file, "w") as f:
                with open(output_file, "r") as md_file:
                    html_content = markdown.markdown(md_file.read(), extensions=["tables", "fenced_code", "codehilite", "toc", "md_in_html"])
                # Load the template file
                with open(template_file, "r") as tf:
                    template_content = tf.read()
                    # Replace the placeholder with the generated HTML content
                final_html = template_content.replace("{{ content }}", html_content)
                f.write(final_html)
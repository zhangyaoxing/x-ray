
from datetime import datetime
import re
from libs.healthcheck.shared import to_markdown_id, irresponsive_nodes
from libs.utils import *
import logging
import importlib
import pkgutil
import markdown

def load_checklist_classes(package_name="libs.healthcheck.check_items"):
    class_map = {}
    package = importlib.import_module(package_name)
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package_name}.{module_name}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type):
                class_map[attr] = obj
    return class_map
CHECKLIST_CLASSES = load_checklist_classes()

class Framework:
    def __init__(self, config: dict):
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._items = []
        self._timestamp = datetime.now().isoformat()

    def _get_output_folder(self, output_folder: str):
        if env == "development":
            batch_folder = output_folder
        else:
            batch_folder = f"{output_folder}{self._checkset_name}-{self._timestamp}/"
            Path(batch_folder).mkdir(parents=True, exist_ok=True)
        return batch_folder
    
    def run_checks(self, checkset_name: str, *args, **kwargs):
        self._checkset_name = checkset_name
        # Create output folder if it doesn't exist
        output_folder = kwargs.get("output_folder", "output/")
        batch_folder = self._get_output_folder(output_folder)
        # Dynamically load the checkset based on the name
        checksets = self._config.get("checksets", {})
        if not checkset_name in checksets:
            self._logger.warning(yellow(f"Checkset '{checkset_name}' not found in configuration. Using default checkset."))
            checkset_name = "default"
        cs = checksets[checkset_name]
        self._logger.info(f"Running checkset: {bold(green(checkset_name))}")

        # The information gathered can be huge sometimes, we always save the information to the file immediately after using.
        # The test result, however, will be kept in memory until the end of the run.
        # The result of each check item will be persisted to a file in the output folder.
        for item_name in cs.get("items", []):
            item_cls = CHECKLIST_CLASSES.get(item_name)
            if not item_cls:
                self._logger.warning(yellow(f"Check item '{item_name}' not found. Skipping."))
                continue
            # The config for the item can be specified in the `item_config` section, under the item class name.
            item_config = self._config.get("item_config", {}).get(item_name, {})
            item = item_cls(batch_folder, item_config)
            self._logger.info(f"Running check item: {bold(green(item.name))}")
            item.test(**kwargs)
            self._items.append(item)

    def output_results(self, output_folder: str = "output/", format: str = "markdown"):
        # output the results to a markdown file
        batch_folder = self._get_output_folder(output_folder)
        output_file = f"{batch_folder}report.md"
        template_file = get_script_path(f"templates/{self._config.get('template', 'standard.html')}")
        self._logger.info(f"Saving results to: {green(output_file)}")

        with open(output_file, "w") as f:
            f.write("# Deployment Health Check\n\n")
            # Display irresponsive nodes
            f.write("## 0 Overview\n\n")
            f.write(f"|<span style='color: red;'>HIGH</span>|<span style='color: orange;'>MEDIUM</span>|<span style='color: green;'>LOW</span>|<span style='color: gray;'>INFO</span>|\n")
            f.write("|---|---|---|---|\n")
            all_test_result = []
            for item in self._items:
                all_test_result.extend(item.test_result["items"])
            all_severity = [result["severity"].name for result in all_test_result]
            high_count = all_severity.count("HIGH")
            medium_count = all_severity.count("MEDIUM")
            low_count = all_severity.count("LOW")
            info_count = all_severity.count("INFO")
            f.write(f"|{high_count}|{medium_count}|{low_count}|{info_count}|\n\n")
            if len(irresponsive_nodes) > 0:
                f.write("The following nodes have been detected as irresponsive during the checks:\n\n")
                for node in irresponsive_nodes:
                    f.write(f"- `{node['host']}`\n")
                f.write("\n**<span style='color: red;'>All checks against the above nodes have been skipped.</span>**\n")
            f.write("## 1 Review Test Results\n\n")
            for i, item in enumerate(self._items):
                title = f"1.{i + 1} {item.name}"
                review_title = f"2.{i + 1} Review {item.name}"
                review_title_id = to_markdown_id(review_title)
                f.write(f"### {title}\n\n")
                f.write(f"{item.description}\n\n")
                f.write(f"[Review Raw Results &rarr;](#{review_title_id})\n\n")
                f.write(item.test_result_markdown)
            
            f.write("## 2 Review Raw Results\n\n")
            for i, item in enumerate(self._items):
                title = f"1.{i + 1} {item.name}"
                title_id = to_markdown_id(title)
                review_title = f"2.{i + 1} Review {item.name}"
                f.write(f"### {review_title}\n\n")
                f.write(f"[&larr; Review Test Results](#{title_id})\n\n")
                f.write(item.review_result_markdown)

        if format == "html":
            html_file = f"{batch_folder}report.html"
            self._logger.info(f"Converting results to HTML format and saving to: {green(html_file)}")
            with open(html_file, "w") as f:
                with open(output_file, "r") as md_file:
                    md_text = md_file.read()
                html = markdown.markdown(md_text, extensions=["tables", "toc"])
                with open(template_file, "r") as template:
                    template_content = template.read()
                    html = template_content.replace("{{ content }}", html)
                f.write(html)

        self._logger.info(bold(green("All checks complete.")))

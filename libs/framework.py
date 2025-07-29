
from datetime import datetime
from libs.utils import *
from libs.checklist.base_item import CATEGORY
import logging
import importlib
import pkgutil

def load_checklist_classes(package_name="libs.checklist"):
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

    def _get_output_folder(self, output_folder: str):
        if env == "development":
            batch_folder = output_folder
        else:
            batch_folder = f"{output_folder}/{self._checkset_name}-{datetime.now().isoformat()}"
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
            item_config = self._config.get("item_config", {}).get(item_name, {})
            item = item_cls(batch_folder, item_config)
            self._logger.info(f"Running check item: {bold(green(item.name))} - {item.description}")
            item.test(kwargs.get("client"))
            self._items.append(item)

    def output_results(self, output_folder: str = "output/"):
        batch_folder = self._get_output_folder(output_folder)
        output_file = f"{batch_folder}/results.md"
        self._logger.info(f"Saving results to {green(output_file)}")

        results = {c.name: {"category_name": c.value, "result_items": []} for c in CATEGORY}
        for item in self._items:
            results.get(item.category.name, {"result_items": []})["result_items"].append(item.test_result_markdown)

        with open(output_file, "w") as f:
            f.write("# Check Results\n\n")
            for category, data in results.items():
                f.write(f"## {data['category_name']}\n\n")
                if not data["result_items"]:
                    f.write("<b style='color: green;'>All pass.</b>\n\n")
                    continue
                for item in data["result_items"]:
                    f.write(item)
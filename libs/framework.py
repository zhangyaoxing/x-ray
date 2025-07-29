
from datetime import datetime
import logging
from libs.utils import *
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

    def run_checks(self, name: str, *args, **kwargs):
        # Create output folder if it doesn't exist
        output_folder = kwargs.get("output_folder", "output/")
        if env == "development":
            batch_folder = output_folder
        else:
            batch_folder = f"{output_folder}/{name}-{datetime.now().isoformat()}"
            Path(batch_folder).mkdir(parents=True, exist_ok=True)
        # Dynamically load the checkset based on the name
        checksets = self._config.get("checksets", {})
        if not name in checksets:
            self._logger.warning(yellow(f"Checkset '{name}' not found in configuration. Using default checkset."))
            cs = checksets.get("default", {})
        else:
            cs = checksets[name]

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
            self._logger.info(f"Running check item: {green(item.name)} - {item.description}")
            item.test(kwargs.get("client"))
            self._items.append(item)
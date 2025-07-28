
import logging
from libs.utils import *

class Framework:
    def __init__(self, config: dict):
        self._config = config
        self._logger = logging.getLogger(__name__)
    
    def _load_checkset(self, name: str):
        checksets = self._config.get("checksets", [])
        if not name in checksets:
            self._logger.warning(yellow(f"Checkset '{name}' not found in configuration. Using default checkset."))
            cs = checksets.get("default", {})
        else:
            cs = checksets[name]

        check_items = []
        for item_name in cs.get("items", []):
            item_cls = globals().get(item_name)
            if not item_cls:
                self._logger.warning(yellow(f"Check item '{item_name}' not found. Skipping."))
                continue
            item = item_cls()
            check_items.append(item)

        self._logger.info(green(f"Loaded checkset '{name}' with {len(check_items)} items."))
        return check_items

    def run_checks(self, name: str, *args, **kwargs):
        self._logger.info(f"Running checks for checkset '{name}'...")
        check_items = self._load_checkset(name)
        for item in check_items:
            item.sample(*args, **kwargs)

        self._logger.info(green("All samples captured."))
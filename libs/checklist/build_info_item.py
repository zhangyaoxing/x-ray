from pymongo import MongoClient
from libs.checklist.base_item import BaseItem, SEVERITY, CATEGORY
from libs.utils import *

class BuildInfoItem(BaseItem):
    def __init__(self, output_folder: str, config: dict = None):
        super().__init__(output_folder, config)
        self._name = "Build Info"
        self._description = "Collects & review server build information."
        self._category = CATEGORY.SERVER_INFO

    def test(self, *args, **kwargs):
        self._logger.info(f"Gathering server build information...")
        client = MongoClient(kwargs.get("client"))
        result = client.admin.command("buildInfo")
        self._logger.info(f"Testing server build information...")
        eol_version = self._config.get("eol_version", [4, 4, 0])
        sample_version = result.get("versionArray", None)
        if not sample_version:
            self._logger.warning(yellow("Failed to retrieve server build information."))
            return False
        if sample_version[0] < eol_version[0] or \
           (sample_version[0] == eol_version[0] and sample_version[1] < eol_version[1]):
            self._test_result.append({
                "severity": SEVERITY.HIGH,
                "message": f"Server version {sample_version} is below EOL version {eol_version}."
            })

        self.sample_result = result
from libs.check_items.base_item import BaseItem
from libs.shared import SEVERITY
from libs.utils import *

class BuildInfoItem(BaseItem):
    def __init__(self, output_folder: str, config: dict = None):
        super().__init__(output_folder, config)
        self._name = "Build Info"
        self._description = "Collects & review server build information."

    def test(self, *args, **kwargs):
        self._logger.info(f"Gathering server build information...")
        client = kwargs.get("client")
        result = client.admin.command("buildInfo")
        self._logger.info(f"Testing server build information...")
        eol_version = self._config.get("eol_version", [4, 4, 0])
        sample_version = result.get("versionArray", None)
        if not sample_version:
            self._logger.warning(yellow("Failed to retrieve server build information."))
            return False
        if sample_version[0] < eol_version[0] or \
           (sample_version[0] == eol_version[0] and sample_version[1] < eol_version[1]):
            self.append_test_result(
                "cluster",
                SEVERITY.HIGH,
                "Server Version EOL",
                f"Server version {sample_version} is below EOL version {eol_version}."
            )

        self.captured_sample = result

    @property
    def review_result(self):
        captured = self.captured_sample
from pymongo.errors import OperationFailure
from libs.check_items.base_item import BaseItem
from libs.shared import check_replset_config, check_replset_status
from libs.utils import *

class ReplicaSetItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Replica Set Information"
        self._description = "Collects and reviews replica set configuration and status."

    def _gather_replset_info(self, client):
        """
        Gather replica set configuration and status.
        """
        try:
            is_master = client.admin.command("isMaster")
            if not is_master.get("setName"):
                self._logger.warning(yellow("This MongoDB instance is not part of a replica set. Skipping..."))
                return None, None
            replset_status = client.admin.command("replSetGetStatus")
            replset_config = client.admin.command("replSetGetConfig")
            return replset_status, replset_config
        except OperationFailure as e:
            self._logger.warning(yellow(f"Failed to gather replica set information: {str(e)}"))
            return None, None

    def test(self, *args, **kwargs):
        self._logger.info("Gathering replica set config / status...")
        client = kwargs.get("client")
        replset_status, replset_config = self._gather_replset_info(client)
        if not replset_status or not replset_config:
            return

        result = check_replset_status(replset_status, self._config)
        for item in result:
            self.append_item_result(item["severity"], item["title"], item["description"])
        result = check_replset_config(replset_config, self._config)
        for item in result:
            self.append_item_result(item["severity"], item["title"], item["description"])

        self.sample_result = {
            "replset_status": replset_status,
            "replset_config": replset_config
        }
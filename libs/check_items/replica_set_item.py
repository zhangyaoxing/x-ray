from pymongo.errors import OperationFailure
from libs.check_items.base_item import BaseItem
from libs.shared import check_oplog_window, check_replset_config, check_replset_status, discover_nodes, gather_oplog_info, gather_replset_info
from libs.utils import *

class ReplicaSetItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Replica Set Information"
        self._description = "Collects and reviews replica set configuration and status."

    def test(self, *args, **kwargs):
        self._logger.info("Gathering replica set config / status...")
        client = kwargs.get("client")
        replset_status, replset_config = gather_replset_info(client)
        if not replset_status or not replset_config:
            return
        # Check replica set status
        result = check_replset_status(replset_status, self._config)
        for item in result:
            self.append_item_result(item["host"], item["severity"], item["title"], item["description"])
        # Check replica set config
        result = check_replset_config(replset_config, self._config)
        for item in result:
            self.append_item_result(item["host"], item["severity"], item["title"], item["description"])

        # Check oplog window
        nodes = discover_nodes(client, kwargs.get("parsed_uri"))
        raw_oplog_info, result = check_oplog_window(nodes, self._config)
        for item in result:
            self.append_item_result(item["host"], item["severity"], item["title"], item["description"])

        self.captured_sample = {
            "replset_status": replset_status,
            "replset_config": replset_config,
            "oplog": raw_oplog_info
        }
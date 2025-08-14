
from libs.check_items.base_item import BaseItem
from libs.shared import SEVERITY
from libs.utils import red
from pymongo.errors import OperationFailure

class ShardKeyItem(BaseItem):
    def __init__(self, output_folder, config=None):
        super().__init__(output_folder, config)
        self._name = "Shard Key Information"
        self._description = "Collects and reviews shard key configuration for collections in a sharded cluster."

    def test(self, *args, **kwargs):
        """
        Main test method to gather shard key information.
        """
        self._logger.info("Gathering shard key information...")
        client = kwargs.get("client")
        
        try:
            collections = list(client.config.collections.find({"_id": {"$ne": 'config.system.sessions'}}))
            for c in collections:
                key = c["key"]
                v = key.get("_id", None)
                if (v == 1 or v == -1) and len(key.keys()) == 1:
                    self.append_item_result(
                        "cluster",
                        SEVERITY.INFO,
                        "Shard Key",
                        f"Collection `{c['_id']}` has the shard key set to `{{_id: {v}}}`. Make sure the value of `_id` is not monotonically increasing or decreasing."
                    )
        except OperationFailure as e:
            self._logger.error(red(f"Error checking shard keys: {e}"))

        self.sample_result = collections
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from libs.check_items.base_item import BaseItem, SEVERITY
from libs.utils import *

"""
This module defines a checklist item for collecting and reviewing collection statistics in MongoDB.
"""
class IndexInfoItem(BaseItem):
    def __init__(self, output_folder, config = None):
        super().__init__(output_folder, config)
        self._name = "Index Information"
        self._description = "Collects & review index statistics."

    def _num_indexes_check(self, ns, index_stats, num_indexes):
        """ Check for the number of indexes in the collection.
        """
        if len(index_stats) > num_indexes:
            self.append_item_result(
                SEVERITY.MEDIUM,
                "Too Many Indexes",
                f"Collection `{ns}` has more than `{num_indexes}` indexes, which can cause potential write performance issues."
            )
    
    def unused_indexes_check(self, ns, index_stats, unused_index_days):
        """
        Check for unused indexes in the collection.
        """
        for index in index_stats:
            if index.get("accesses", {}).get("ops", 0) == 0:
                last_used = index.get("accesses", {}).get("since", None)
                if last_used:
                    if (datetime.now() - last_used).days > unused_index_days:
                        self.append_item_result(
                            SEVERITY.MEDIUM,
                            "Unused Index",
                            f"Index `{index.get('name')}` in collection `{ns}` has not been used for more than `{unused_index_days}` days."
                        )

    def _redundant_indexes_check(self, ns, indexes):
        """
        Check for redundant indexes in the collection.
        """
        def is_redundant(index1, index2):
            # These options must be identical for indexes to be considered redundant
            OPTIONS = ["unique", "sparse", "partialFilterExpression", "collation", "hidden"]
            for o in OPTIONS:
                if index1.get(o) != index2.get(o):
                    return False
            # Check if the keys are identical or if one is a prefix of the other
            key1 = "_".join([f"{k}_{v}" for k, v in index1["key"].items()])
            key2 = "_".join([f"{k}_{v}" for k, v in index2["key"].items()])

            # If key1 == key2, it's being compared to itself, so skip
            return key1 != key2 and key2.startswith(key1)

        reverse_indexes = []
        for index in indexes:
            reverse_index = {k: v for k, v in index.items() if k != "key"}
            reverse_index["key"] = {k: (v * -1 if isinstance(v, (int, float)) else v) for k, v in index["key"].items()}
            reverse_indexes.append(reverse_index)
        index_targets = indexes + reverse_indexes
        for index in indexes:
            for target in index_targets:
                if is_redundant(index, target):
                    self.append_item_result(
                        SEVERITY.MEDIUM,
                        "Redundant Index",
                        f"Index `{index.get('name')}` in collection `{ns}` is redundant with index `{target.get('name')}`."
                    )
                    break

    def test(self, *args, **kwargs):
        self._logger.info(f"Gathering index info...")
        client = kwargs.get("client")
        dbs = client.admin.command("listDatabases").get("databases", [])
        all_index_stats = []
        for db_obj in dbs:
            db_name = db_obj.get("name")
            if db_name in ["admin", "local", "config"]:
                self._logger.info(f"Skipping system database: {db_name}")
                continue
            db = client[db_name]
            collections = db.list_collections()
            unused_index_days = self._config.get("unused_index_days", 7)
            num_indexes = self._config.get("num_indexes", 10)

            for coll_info in collections:
                coll_name = coll_info.get("name")
                coll_type = coll_info.get("type", "collection")
                if coll_type != "collection":
                    self._logger.debug(f"Skipping non-collection type: {coll_name} ({coll_type})")
                    continue
                if coll_name.startswith("system."):
                    self._logger.debug(f"Skipping system collection: {db_name}.{coll_name}")
                    continue
                self._logger.info(f"Gathering index info of collection: `{db_name}.{coll_name}`")
                ns = f"{db_name}.{coll_name}"
                try:
                    # Check for number of indexes
                    index_stats = list(db[coll_name].aggregate([
                        {"$indexStats": {}}
                    ]))
                    all_index_stats.append({ns: index_stats})
                    self._num_indexes_check(ns, index_stats, num_indexes)

                    # Check for unused indexes
                    self.unused_indexes_check(ns, index_stats, unused_index_days)

                    # Check for redundant indexes
                    # indexes = db.command("listIndexes", coll_name).get("cursor", {}).get("firstBatch", [])
                    indexes = [index["spec"] for i, index in enumerate(index_stats)]
                    self._redundant_indexes_check(ns, indexes)
                    
                except Exception as e:
                    self._logger.error(red(f"Failed to gather index info of collection '{ns}': {str(e)}"))

            self.sample_result = all_index_stats
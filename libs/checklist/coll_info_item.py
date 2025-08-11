from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from libs.checklist.base_item import BaseItem, SEVERITY, CATEGORY
from libs.utils import *

"""
This module defines a checklist item for collecting and reviewing collection statistics in MongoDB.
"""
class CollInfoItem(BaseItem):
    def __init__(self, output_folder, config = None):
        super().__init__(output_folder, config)
        self._name = "Collection Information"
        self._description = "Collects & review collection statistics."
        self._category = CATEGORY.DATA

    def _fragmentation_check(self, stats):
        """
        Check for fragmentation in the collection.
        """
        def get_details(id, s):
            detail = {
                "id": id,
                "size": s.get("size", 0),
                "storage_size": s.get("storageSize", 0),
                "coll_reusable": s["wiredTiger"]["block-manager"]["file bytes available for reuse"],
                "total_index_size": s.get("totalIndexSize", 0),
                "index_reusable": 0
            }
            if "indexDetails" in s:
                detail["index_reusable"] = sum(
                    index["block-manager"]["file bytes available for reuse"] for index in s["indexDetails"].values()
                )
                return detail
            else:
                self._logger.warning(yellow(f"No index details found for collection {id}. Skipping index space calculation."))
                return None

        results = []
        if "sharded" in stats and stats["sharded"]:
            for name, shard in stats.get("shards", []).items():
                results.append(get_details(f"{name}-{stats['ns']}", shard))
        else:
            results.append(get_details(stats["ns"], stats))

        return results
        
    def test(self, *args, **kwargs):
        self._logger.info(f"Gathering collection statistics...")
        client = kwargs.get("client")
        dbs = client.admin.command("listDatabases").get("databases", [])
        for db_obj in dbs:
            db_name = db_obj.get("name")
            if db_name in ["admin", "local", "config"]:
                self._logger.info(f"Skipping system database: {db_name}")
                continue
            db = client[db_name]
            collections = db.list_collection_names()
            obj_size_bytes = self._config.get("obj_size_kb", 32) * 1024
            unused_index_days = self._config.get("unused_index_days", 7)
            num_indexes = self._config.get("num_indexes", 10)
  
            for coll_name in collections:
                if coll_name.startswith("system."):
                    self._logger.debug(f"Skipping system collection: {db_name}.{coll_name}")
                    continue
                self._logger.info(f"Gathering stats for collection: `{db_name}.{coll_name}`")
                try:
                    stats = db.command("collStats", coll_name, indexDetails=True)
                    # Check for average object size
                    if stats.get("avgObjSize", 0) > obj_size_bytes:
                        self._test_result.append({
                            "severity": SEVERITY.MEDIUM,
                            "message": f"Collection `{db_name}.{coll_name}` has average object size `{stats.get('avgObjSize', 0) / 1024} KB`, which is larger than `{self._config.get('obj_size_kb', 32)} KB`."
                        })

                    # Check for fragmentation
                    fragmentation = self._fragmentation_check(stats)
                    for detail in fragmentation:
                        storage_size = detail.get("storage_size", 0)
                        total_index_size = detail.get("total_index_size", 0)
                        coll_reusable = detail.get("coll_reusable", 0)
                        index_reusable = detail.get("index_reusable", 0)
                        coll_frag = coll_reusable / storage_size if storage_size else 0
                        index_frag = index_reusable / total_index_size if total_index_size else 0
                        medium_threshold = self._config.get("fragmentation_medium", 0.5)
                        high_threshold = self._config.get("fragmentation_high", 0.75)
                        if coll_frag > medium_threshold:
                            self._test_result.append({
                                "severity": SEVERITY.MEDIUM if coll_frag < high_threshold else SEVERITY.HIGH,
                                "message": f"Collection `{detail['id']}` has a higher fragmentation: `{coll_frag:.2%}` than threshold `{(medium_threshold if coll_frag < high_threshold else high_threshold):.2%}`."
                            })
                        if index_frag > medium_threshold:
                            self._test_result.append({
                                "severity": SEVERITY.MEDIUM if index_frag < high_threshold else SEVERITY.HIGH,
                                "message": f"Collection `{detail['id']}` has a higher index fragmentation: `{index_frag:.2%}` than threshold `{(medium_threshold if index_frag < high_threshold else high_threshold):.2%}`."
                            })

                    index_stats = list(db[coll_name].aggregate([
                        {"$indexStats": {}}
                    ]))
                    # Check for number of indexes
                    if len(index_stats) > num_indexes:
                        self._test_result.append({
                            "severity": SEVERITY.MEDIUM,
                            "message": f"Collection `{db_name}.{coll_name}` has more than `{num_indexes}` indexes, which may lead to write performance issues."
                        })
                    # Check for unused indexes
                    for index in index_stats:
                        if index.get("accesses", {}).get("ops", 0) == 0:
                            last_used = index.get("accesses", {}).get("since", None)
                            if last_used:
                                if (datetime.now() - last_used).days > unused_index_days:
                                    self._test_result.append({
                                        "severity": SEVERITY.LOW,
                                        "message": f"Index `{index.get('name')}` in collection `{db_name}.{coll_name}` has not been used for more than `{unused_index_days}` days."
                                    })
                    
                except Exception as e:
                    if isinstance(e, OperationFailure) and e.code == 166:
                        self._logger.warning(yellow(f"Collection '{db_name}.{coll_name}' is a view, skipping stats collection."))
                    else:
                        self._logger.error(red(f"Failed to gather stats for collection '{db_name}.{coll_name}': {str(e)}"))